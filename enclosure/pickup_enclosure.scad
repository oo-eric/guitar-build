// Strat Single-Coil Pickup Enclosure for 6x Ubertar 77HC Single-String Pickups
// All dimensions in mm

// === ENCLOSURE OUTER DIMENSIONS (Standard Strat Single-Coil) ===
cover_length = 69.5;       // along strings direction
cover_width  = 17.5;       // across strings
cover_height = 15.0;       // total depth
wall_thickness = 1.6;      // shell wall thickness
bottom_thickness = 1.2;    // floor thickness

// === MOUNTING EARS ===
ear_length = 4.0;          // how far ears extend beyond cover body
ear_width  = 10.0;         // ear width (along cover_width axis)
ear_thickness = 3.0;       // ear height/thickness
screw_hole_dia = 3.2;      // #4 screw clearance
ear_spacing = 77.8;        // center-to-center between mounting holes

// === PICKUP SLOTS (adjust to your 77HC measurements) ===
num_pickups = 6;
pickup_width  = 8.0;       // each 77HC pickup body width — MEASURE AND ADJUST
pickup_height = 10.0;      // each 77HC pickup body height — MEASURE AND ADJUST
pickup_depth  = 12.0;      // how deep the pocket is (cover_height - bottom_thickness)
slot_tolerance = 0.3;      // clearance per side for fit

// === STRING SPACING ===
// Standard Strat: ~10.5mm at bridge, but 6 pickups must fit in cover_length
// Auto-calculated from cover_length and number of pickups
string_spacing = (cover_length - 2 * wall_thickness - pickup_width - 2 * slot_tolerance) / (num_pickups - 1);

// === WIRE CHANNEL ===
wire_channel_dia = 3.0;    // diameter of wire exit holes in bottom
wire_exit = "bottom";       // "bottom" or "side"

// === CORNER ROUNDING ===
corner_radius = 2.0;

// ============================================================
// MODULES
// ============================================================

module rounded_box(l, w, h, r) {
    hull() {
        for (x = [r, l - r])
            for (y = [r, w - r])
                translate([x, y, 0])
                    cylinder(h = h, r = r, $fn = 24);
    }
}

module enclosure_shell() {
    difference() {
        // Outer shell
        rounded_box(cover_length, cover_width, cover_height, corner_radius);

        // Hollow interior
        translate([wall_thickness, wall_thickness, bottom_thickness])
            rounded_box(
                cover_length - 2 * wall_thickness,
                cover_width  - 2 * wall_thickness,
                cover_height,  // cut through top
                max(corner_radius - wall_thickness, 0.5)
            );
    }
}

module pickup_slot(x_pos) {
    sw = pickup_width + 2 * slot_tolerance;
    sh = cover_width - 2 * wall_thickness;
    translate([x_pos - sw / 2, wall_thickness, bottom_thickness])
        cube([sw, sh, pickup_depth + 1]);  // +1 to cut through top
}

module wire_hole(x_pos) {
    if (wire_exit == "bottom") {
        translate([x_pos, cover_width / 2, -1])
            cylinder(d = wire_channel_dia, h = bottom_thickness + 2, $fn = 16);
    } else {
        // Side exit
        translate([x_pos, -1, bottom_thickness + pickup_depth / 2])
            rotate([-90, 0, 0])
                cylinder(d = wire_channel_dia, h = wall_thickness + 2, $fn = 16);
    }
}

module mounting_ear(x_pos) {
    // Ear pad
    translate([x_pos - ear_width / 2, cover_width, 0])
        difference() {
            cube([ear_width, ear_length, ear_thickness]);
            // Screw hole
            translate([ear_width / 2, ear_length / 2, -1])
                cylinder(d = screw_hole_dia, h = ear_thickness + 2, $fn = 24);
        }

    // Mirror on other side
    translate([x_pos - ear_width / 2, -ear_length, 0])
        difference() {
            cube([ear_width, ear_length, ear_thickness]);
            translate([ear_width / 2, ear_length / 2, -1])
                cylinder(d = screw_hole_dia, h = ear_thickness + 2, $fn = 24);
        }
}

module pickup_enclosure() {
    // Calculate first pickup X position (centered in cover)
    first_x = wall_thickness + (pickup_width / 2) + slot_tolerance;

    difference() {
        union() {
            enclosure_shell();

            // Mounting ears at standard spacing
            ear_x1 = cover_length / 2 - ear_spacing / 2;
            ear_x2 = cover_length / 2 + ear_spacing / 2;
            mounting_ear(ear_x1);
            mounting_ear(ear_x2);
        }

        // Cut pickup slots
        for (i = [0 : num_pickups - 1]) {
            x = first_x + i * string_spacing;
            pickup_slot(x);
            wire_hole(x);
        }
    }

    // Info echo
    echo(str("String spacing: ", string_spacing, " mm"));
    echo(str("Total slot width per pickup: ", pickup_width + 2 * slot_tolerance, " mm"));
}

// ============================================================
// RENDER
// ============================================================
pickup_enclosure();
