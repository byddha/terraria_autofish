// Find the module containing Mono exports.
// Wine/Proton: "libmono-2.0-x86.dll" (32-bit, stdcall)
// Linux native: "Terraria.bin.x86_64" (64-bit, default calling convention)
var mono = null;
var abi = "default";
var ptrSize = Process.pointerSize;

try {
    mono = Process.getModuleByName("libmono-2.0-x86.dll");
    abi = "stdcall";
} catch (e) {
    mono = Process.getModuleByName("Terraria.bin.x86_64");
}

// On the main executable, getExportByName fails — build a lookup table instead.
var exportMap = {};
mono.enumerateExports().forEach(function (exp) {
    if (exp.name.indexOf("mono_") === 0) {
        exportMap[exp.name] = exp.address;
    }
});

function mf(name, ret, args) {
    var addr = exportMap[name];
    if (!addr) throw new Error("Mono export not found: " + name);
    return new NativeFunction(addr, ret, args, abi);
}

var mono_get_root_domain = mf("mono_get_root_domain", "pointer", []);
var mono_thread_attach = mf("mono_thread_attach", "pointer", ["pointer"]);
var mono_thread_detach = mf("mono_thread_detach", "void", ["pointer"]);
var mono_image_loaded = mf("mono_image_loaded", "pointer", ["pointer"]);
var mono_class_from_name = mf("mono_class_from_name", "pointer", ["pointer", "pointer", "pointer"]);
var mono_class_get_field_from_name = mf("mono_class_get_field_from_name", "pointer", ["pointer", "pointer"]);
var mono_field_get_offset = mf("mono_field_get_offset", "int", ["pointer"]);
var mono_class_vtable = mf("mono_class_vtable", "pointer", ["pointer", "pointer"]);
var mono_vtable_get_static_field_data = mf("mono_vtable_get_static_field_data", "pointer", ["pointer"]);

// Attach to Mono, resolve all field offsets, then detach.
// Detaching is critical — if we stay attached, Mono's GC will deadlock
// trying to suspend this thread during stop-the-world collection.
var domain = mono_get_root_domain();
var thread = mono_thread_attach(domain);

var image = mono_image_loaded(Memory.allocUtf8String("Terraria"));
var ns = Memory.allocUtf8String("Terraria");

var mainClass = mono_class_from_name(image, ns, Memory.allocUtf8String("Main"));
var vtable = mono_class_vtable(domain, mainClass);
var mainStatic = mono_vtable_get_static_field_data(vtable);

var myPlayerOff = mono_field_get_offset(mono_class_get_field_from_name(mainClass, Memory.allocUtf8String("myPlayer")));
var projOff = mono_field_get_offset(mono_class_get_field_from_name(mainClass, Memory.allocUtf8String("projectile")));

var projClass = mono_class_from_name(image, ns, Memory.allocUtf8String("Projectile"));
var activeOff = mono_field_get_offset(mono_class_get_field_from_name(projClass, Memory.allocUtf8String("active")));
var ownerOff = mono_field_get_offset(mono_class_get_field_from_name(projClass, Memory.allocUtf8String("owner")));
var bobberOff = mono_field_get_offset(mono_class_get_field_from_name(projClass, Memory.allocUtf8String("bobber")));
var aiOff = mono_field_get_offset(mono_class_get_field_from_name(projClass, Memory.allocUtf8String("ai")));
var localAIOff = mono_field_get_offset(mono_class_get_field_from_name(projClass, Memory.allocUtf8String("localAI")));

mono_thread_detach(thread);

// Mono array header:
// 32-bit: vtable(4) + pad(4) + pad(4) + len(4) = 16 bytes
// 64-bit: vtable(8) + pad(8) + pad(8) + len(8) = 32 bytes
var arrayHeaderSize = ptrSize === 4 ? 16 : 32;
// ai[1] offset from start of float array: header + sizeof(float)
var ai1Off = arrayHeaderSize + 4;

// After detach, raw pointer reads still work — we're just reading
// process memory without being registered as a Mono thread.
rpc.exports = {
    // Scan all 1000 projectile slots for the local player's bobber.
    // Returns the bobber's ai[1] value (negative = fish biting), or null.
    checkBite: function () {
        var myPlayer = mainStatic.add(myPlayerOff).readS32();
        var projArray = mainStatic.add(projOff).readPointer();
        var elemBase = projArray.add(arrayHeaderSize);

        for (var i = 0; i < 1000; i++) {
            var proj = elemBase.add(i * ptrSize).readPointer();
            if (proj.isNull()) continue;
            if (!proj.add(activeOff).readU8()) continue;
            if (proj.add(ownerOff).readS32() !== myPlayer) continue;
            if (!proj.add(bobberOff).readU8()) continue;

            var aiArr = proj.add(aiOff).readPointer();
            var ai1 = aiArr.add(ai1Off).readFloat();
            var localAIArr = proj.add(localAIOff).readPointer();
            var localAI1 = localAIArr.add(ai1Off).readFloat();
            return [ai1, localAI1];
        }
        return null;
    },
};

send("ready");
