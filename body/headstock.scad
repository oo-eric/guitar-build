// Headstock outline studies — 6-inline vs 3+3 on a 4.5 x 7.5" paddle.
//
// Origin: X centred on the string centreline, Y = 0 at the NUT FACE.
// Geometry (post positions, splay) comes from scripts/headstock_layout.py —
// change values there first, then mirror them here.
//
//   layout = 1  ->  6-inline
//   layout = 2  ->  3+3
//
//   openscad -D layout=1 -o out.png --viewall --projection=o headstock.scad

layout   = 2;
soften   = 4;     // corner radius. Smaller than the body's 8 —
                  // this part is a third the size, so 8 erased the shape.
show_ref = true;  // paddle boundary + string paths + post holes
$fn      = 64;

// ---------------------------------------------------------------- paddle
paddle_w = 114.3;   // 4.5"
paddle_l = 190.5;   // 7.5", all usable — nut face to tip

// ------------------------------------------------------------ hardware
post_hole   = 10.0;   // modern sealed tuner
string_gauge = 1.2;   // drawn width, for the preview only

// string centres at the nut, low E first
nut_x = [-18, -10.8, -3.6, 3.6, 10.8, 18];

// post centres, from headstock_layout.py's minimax offset solve
posts_6 = [[-13.1, 25], [-13.1, 52], [-13.1, 79],
           [-13.1, 106], [-13.1, 133], [-13.1, 160]];

// 3+3: OUTER strings take the NEAR posts so the inner pair (D, G) get the
// long run and stay near straight. Reversing this puts 30 deg on the G.
posts_3 = [[-15, 25], [-15, 60], [-15, 95],     // E  A  D
           [ 15, 95], [ 15, 60], [ 15, 25]];    // G  B  e

// Round convex AND concave corners at radius r, keeping overall size.
module soften_corners(r) {
  if (r <= 0) children();
  else offset(r = -r) offset(r = 2 * r) offset(r = -r) children();
}

// ------------------------------------------------------------- outlines

// Bass side carries the whole tuner run, so it does all the flaring.
// Treble side stays quiet. Uses 175 of the 190.5 mm available.
module outline_6inline() {
  polygon([
    [-23, 0], [-31, 17], [-41, 40], [-46, 68],
    [-40, 96],                                  // waist — offset-guitar echo
    [-46, 124], [-44, 152], [-36, 172], [-24, 184],
    [-9, 190], [6, 189], [18, 183], [26, 171],
    [30, 153], [30, 128], [28, 100], [26, 72], [25, 46], [24, 22], [23, 0]
  ]);
}

// Symmetric, soft shoulders, a shallow open-book dip at the crown.
// Only 141 mm long — deliberately does NOT fill the paddle.
module outline_3x3() {
  polygon([
    [-23, 0], [-28, 14], [-33, 34], [-35, 60], [-34, 88], [-31, 110],
    [-24, 128], [-14, 139], [-6, 143],
    [0, 132],                                   // open-book dip
    [6, 143], [14, 139], [24, 128], [31, 110], [34, 88], [35, 60],
    [33, 34], [28, 14], [23, 0]
  ]);
}

// --------------------------------------------------------------- preview

module string_paths(posts) {
  for (i = [0:5])
    hull() {
      translate([nut_x[i], 0])    circle(d = string_gauge);
      translate(posts[i])         circle(d = string_gauge);
    }
}

module post_holes(posts) {
  for (p = posts) translate(p) circle(d = post_hole);
}

// The blank, as a thin frame — shows how much wood the shape leaves behind.
module paddle_ref() {
  difference() {
    translate([-paddle_w / 2, 0]) square([paddle_w, paddle_l]);
    translate([-paddle_w / 2 + 0.8, 0.8])
      square([paddle_w - 1.6, paddle_l - 1.6]);
  }
}

posts = (layout == 1) ? posts_6 : posts_3;

union() {
  difference() {
    if (layout == 1) soften_corners(soften) outline_6inline();
    else             soften_corners(soften) outline_3x3();

    if (show_ref) {
      post_holes(posts);
      string_paths(posts);
    }
  }
  if (show_ref) paddle_ref();
}
