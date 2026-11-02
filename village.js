// The village layout as drawn: a green with a lane around it, a high street in front of
// the trading post and café, and lanes and footpaths out to each place.
//
// This is scenery only. Crow's simulation never reads it: his places, objects, trees and
// coordinates live in his save and are unchanged. Nothing here blocks walking.
//
// To grow the village, add a lane (a list of points) or use one of the PLOTS below for a
// new building. A building he should be able to see and use must also be added to his
// world in town.py, like the café and trading post.

export const VILLAGE = {
  green: {x: 0, z: 0, r: 7},
  ringLane: {inner: 7, outer: 8.3},
  // [width, colour, points...]. Points are [x, z]. Widths in metres.
  lanes: [
    // High Street: in front of the trading post and café, with a small market square.
    {name: 'High Street', width: 2.3, kind: 'street', points: [[-6.6, -13.3], [3, -13.3], [12.8, -13.3]]},
    {name: 'Garden Lane', width: 1.4, kind: 'lane', points: [[-6.6, -13.3], [-12.6, -13.6]]},
    {name: 'Church Lane', width: 1.8, kind: 'lane', points: [[0.4, -8.1], [1.6, -12.2]]},
    {name: 'Cabin Lane', width: 1.5, kind: 'lane', points: [[-6.4, -3.9], [-8.6, -6.1], [-10, -7.4]]},
    {name: 'Back Lane', width: 1.2, kind: 'lane', points: [[-8.6, -6.1], [-6.3, -8.4], [-6.3, -12.4]]},
    {name: 'Library Lane', width: 1.5, kind: 'lane', points: [[-6.7, 3.6], [-9.4, 5.2], [-11, 6.6]]},
    {name: 'Workshop Path', width: 1.4, kind: 'lane', points: [[0, 8.1], [0, 10.6]]},
    {name: 'Chime Walk', width: .9, kind: 'footpath', points: [[0, 10.2], [-2.6, 12.2], [-4.4, 13.2]]},
    {name: 'Spring Path', width: 1.1, kind: 'footpath', points: [[-8.1, -0.6], [-12, -1.2], [-15.2, -1.4]]},
    {name: 'Butts Path', width: 1.1, kind: 'footpath', points: [[5.5, -5.6], [8.2, -6.6], [10, -7.6]]},
    {name: 'Stones Path', width: .9, kind: 'footpath', points: [[12.8, -13.3], [13.4, -13.6]]},
    {name: 'Wood Track', width: 1.4, kind: 'track', points: [[6.4, 4.1], [9.6, 6.6], [13, 9.2], [15.4, 10.6]]},
  ],
  square: {x: 3, z: -11.9, w: 4.4, d: 2.6},
  // Open places a new building could go later. Check his trees and objects first.
  PLOTS: [
    {id: 'high_street_middle', x: 3, z: -17.5, note: 'between the trading post and café, facing the High Street'},
    {id: 'green_west', x: -14.5, z: -6.5, note: 'west of the cabin, off Cabin Lane'},
    {id: 'green_north_east', x: 7.5, z: 12.5, note: 'past the workshop, off the Wood Track'},
  ],
};

const COLOURS = {street: '#a8a07c', lane: '#a39d77', footpath: '#9b9472', track: '#8f8461'};

export function buildVillage({T, scene, mat}) {
  const flat = (geo, colour, x, y, z) => {
    const m = new T.Mesh(geo, mat(colour));
    m.rotation.x = -Math.PI / 2;
    m.position.set(x, y, z);
    m.receiveShadow = true;
    m.castShadow = false;
    scene.add(m);
    return m;
  };
  const {green, ringLane, lanes, square} = VILLAGE;
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
