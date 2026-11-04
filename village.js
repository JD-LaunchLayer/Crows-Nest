// The village layout as drawn: a green with a lane around it, a high street in front of
// the trading post and café, and lanes and footpaths out to each place.
//
// v0.34.0: the green, lanes and square come from the one world layout (data/world_layout.json), the
// same file his world is built from. To grow the village, add a lane there (a list of points) or use one
// of its plots for a new building; a building he should be able to use must also be added to his world
// in town.py, like the café and trading post.


const COLOURS = {street: '#a8a07c', lane: '#a39d77', footpath: '#9b9472', track: '#8f8461'};

export function buildVillage({T, scene, mat, layout}) {
  const flat = (geo, colour, x, y, z) => {
    const m = new T.Mesh(geo, mat(colour));
    m.rotation.x = -Math.PI / 2;
    m.position.set(x, y, z);
    m.receiveShadow = true;
    m.castShadow = false;
    scene.add(m);
    return m;
  };
  const {green, ring_lane: ringLane, lanes, square} = layout;
  flat(new T.CircleGeometry(green.r, 48), '#7f8f5f', green.x, -.015, green.z);
  flat(new T.RingGeometry(ringLane.inner, ringLane.outer, 64), COLOURS.lane, green.x, .012, green.z);
  // A low verge stone edging the green.
  flat(new T.RingGeometry(ringLane.inner - .12, ringLane.inner, 64), '#b9b394', green.x, .016, green.z);
  for (const lane of lanes) {
    const colour = COLOURS[lane.kind] || COLOURS.lane;
    const y = lane.kind === 'street' ? .02 : .014;
    for (let i = 0; i < lane.points.length - 1; i++) {
      const [ax, az] = lane.points[i], [bx, bz] = lane.points[i + 1];
      const length = Math.hypot(bx - ax, bz - az);
      const geo = new T.PlaneGeometry(lane.width, length).rotateX(-Math.PI / 2);
      const seg = new T.Mesh(geo, mat(colour));
      seg.position.set((ax + bx) / 2, y, (az + bz) / 2);
      seg.rotation.y = Math.atan2(bx - ax, bz - az);
      seg.receiveShadow = true;
      scene.add(seg);
      // Round the joints so bends read as lanes, not stuck-together boards.
      flat(new T.CircleGeometry(lane.width / 2, 16), colour, bx, y, bz);
    }
    const [sx, sz] = lane.points[0];
    flat(new T.CircleGeometry(lane.width / 2, 16), colour, sx, y, sz);
  }
  flat(new T.PlaneGeometry(square.w, square.d), '#b1a984', square.x, .022, square.z);
}
