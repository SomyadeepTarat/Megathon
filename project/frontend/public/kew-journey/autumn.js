import * as THREE from './vendor/three.module.js';

export function createAutumnScene(canvas, destination, logoSvg) {
  const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true, powerPreference: 'low-power' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
  const scene = new THREE.Scene();
  renderer.setClearColor('#f8f7f3', 0);
  const camera = new THREE.PerspectiveCamera(42, 1, .1, 80);
  camera.position.z = 22;
  scene.add(new THREE.HemisphereLight('#fff3da', '#5a6042', 2.4));
  const light = new THREE.DirectionalLight('#fff0ce', 2.5);
  light.position.set(-8, 12, 15); scene.add(light);
  const shape = new THREE.Shape();
  shape.moveTo(0, -.65);
  shape.bezierCurveTo(-.65, -.25, -.8, .45, 0, .85);
  shape.bezierCurveTo(.8, .45, .65, -.25, 0, -.65);
  const geometry = new THREE.ShapeGeometry(shape, 8);
  const positions = geometry.attributes.position;
  for (let i = 0; i < positions.count; i++) {
    const x = positions.getX(i), y = positions.getY(i);
    positions.setZ(i, .25 * x * x + .1 * Math.sin(y * 3));
  }
  geometry.computeVertexNormals();
  const materials = ['#aa5b2f', '#ca873c', '#d5a24e', '#8d4932', '#7b8244'].map(color => new THREE.MeshStandardMaterial({ color, roughness: .85, side: THREE.DoubleSide }));
  const count = window.innerWidth < 700 ? 700 : 1200;
  const fieldMaterial = new THREE.MeshStandardMaterial({ color: '#ffffff', roughness: .85, side: THREE.DoubleSide, transparent: true });
  const field = new THREE.InstancedMesh(geometry, fieldMaterial, count);
  field.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  scene.add(field);
  const dummy = new THREE.Object3D();
  const leaves = Array.from({ length: count }, (_, i) => {
    const seed = n => ((Math.sin(i * 127.1 + n * 311.7) * 43758.5453) % 1 + 1) % 1;
    field.setColorAt(i, new THREE.Color(['#aa5b2f', '#ca873c', '#d5a24e', '#8d4932', '#7b8244'][i % 5]));
    return { x: seed(3), y: seed(4), z: seed(5) * 12 - 5, size: .18 + seed(1) * .45, speed: 6 + seed(6) * 5, phase: seed(7) * Math.PI * 2 };
  });
  const chosenMaterial = new THREE.MeshStandardMaterial({ color: '#ca873c', side: THREE.DoubleSide, roughness: .8, transparent: true });
  // A filled leaf gradually opens into the actual logo's stroked outline.
  const segments = 96;
  const morphGeometry = new THREE.BufferGeometry();
  const startVertices = [], endVertices = [], indices = [];
  const paths = Array.from(logoSvg?.querySelectorAll('path') ?? []);
  const outline = paths.sort((a, b) => b.getTotalLength() - a.getTotalLength())[0];
  const viewBox = logoSvg?.viewBox.baseVal;
  const boxWidth = viewBox?.width || 24, boxHeight = viewBox?.height || 24;
  const stroke = Number(logoSvg?.getAttribute('stroke-width') || 2) / boxHeight * 1.5;
  const leafCurve = shape.getPoints(96);
  const contour = new THREE.CurvePath();
  for (let i = 1; i < leafCurve.length; i++) contour.add(new THREE.LineCurve(leafCurve[i - 1], leafCurve[i]));
  for (let i = 0; i <= segments; i++) {
    const u = i / segments;
    const initial = contour.getPoint(u);
    const length = outline?.getTotalLength() || 1;
    const point = outline?.getPointAtLength(u * length);
    const before = outline?.getPointAtLength(Math.max(0, u * length - .02));
    const after = outline?.getPointAtLength(Math.min(length, u * length + .02));
    const tangent = new THREE.Vector2((after?.x ?? 1) - (before?.x ?? 0), -((after?.y ?? 0) - (before?.y ?? 0))).normalize();
    const normal = new THREE.Vector2(-tangent.y, tangent.x).multiplyScalar(stroke / 2);
    const x = point ? (point.x / boxWidth - .5) * 1.5 : initial.x;
    const y = point ? (.5 - point.y / boxHeight) * 1.5 : initial.y;
    startVertices.push(initial.x, initial.y, .25 * initial.x ** 2 + .1 * Math.sin(initial.y * 3), 0, 0, 0);
    endVertices.push(x + normal.x, y + normal.y, 0, x - normal.x, y - normal.y, 0);
    if (i < segments) { const n = i * 2; indices.push(n, n + 1, n + 2, n + 1, n + 3, n + 2); }
  }
  morphGeometry.setAttribute('position', new THREE.Float32BufferAttribute(startVertices, 3));
  morphGeometry.setIndex(indices);
  morphGeometry.computeVertexNormals();
  const chosen = new THREE.Mesh(morphGeometry, chosenMaterial);
  const veinGroup = new THREE.Group();
  const veinMaterial = new THREE.MeshBasicMaterial({ color: '#2d493e', transparent: true, opacity: 0, depthTest: false });
  for (const path of paths.slice(1)) {
    const points = Array.from({ length: 49 }, (_, i) => {
      const p = path.getPointAtLength(path.getTotalLength() * i / 48);
      return new THREE.Vector3((p.x / boxWidth - .5) * 1.5, (.5 - p.y / boxHeight) * 1.5, .001);
    });
    const vein = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(points), 48, stroke / 2, 5, false), veinMaterial);
    vein.renderOrder = 3; veinGroup.add(vein);
  }
  chosen.add(veinGroup);
  chosen.visible = false; scene.add(chosen);
  let selected = -1, from, fromRotation, fromSize;
  const ease = t => { t = Math.max(0, Math.min(1,t)); return t*t*(3-2*t); };
  let span = 20;
  function resize() {
    renderer.setSize(window.innerWidth, window.innerHeight, false);
    camera.aspect = window.innerWidth / window.innerHeight; camera.updateProjectionMatrix();
    span = 20 * camera.aspect;
  }
  resize();
  return {
    resize,
    render(seconds, handoff = 0) {
      const fallHeight = 25;
      // Preserve the original small, airy leaves with a denser layered fall.
      for (let i = 0; i < count; i++) {
        const { x, y, z, speed, phase, size } = leaves[i];
        dummy.position.set((x - .5) * (span + 12) + Math.sin(seconds * 1.2 + phase) * 1.4, 12.5 - ((y * fallHeight + seconds * speed) % fallHeight), z);
        dummy.rotation.set(seconds * 1.4 + phase, Math.sin(seconds * 1.7 + phase) * 1.8, Math.sin(seconds * 2 + phase) * .9);
        dummy.scale.setScalar(i === selected ? .00001 : size);
        dummy.updateMatrix(); field.setMatrixAt(i, dummy.matrix);
      }
      field.instanceMatrix.needsUpdate = true;
      if (seconds >= 1.65 && selected < 0) {
        const candidates = leaves.map((leaf, i) => ({leaf,i})).filter(({leaf}) => {
          const y = 12.5 - ((leaf.y * fallHeight + seconds * leaf.speed) % fallHeight);
          return leaf.x > .35 && leaf.x < .65 && Math.abs(y) < 3 && leaf.z > 2;
        });
        selected = candidates[Math.floor(Math.random() * candidates.length)]?.i ?? 0;
        field.getMatrixAt(selected, dummy.matrix);
        dummy.matrix.decompose(chosen.position, chosen.quaternion, chosen.scale);
        from = chosen.position.clone(); fromRotation = chosen.quaternion.clone(); fromSize = chosen.scale.x;
        chosen.visible = true; chosen.renderOrder = 2; chosenMaterial.depthTest = false;
      }
      if (selected >= 0) {
        const t = ease((seconds - 1.65) / 1.5);
        const rect = destination();
        const z = from.z;
        const distance = camera.position.z - z;
        const height = 2 * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) * distance;
        const viewport = canvas.getBoundingClientRect();
        const end = new THREE.Vector3(((rect.left + rect.width / 2 - viewport.left) / viewport.width - .5) * height * camera.aspect, (.5 - (rect.top + rect.height / 2 - viewport.top) / viewport.height) * height, z);
        chosen.position.lerpVectors(from, end, t);
        if (t < 1) chosen.position.x += Math.sin(t * Math.PI) * 1.8;
        chosen.quaternion.slerpQuaternions(fromRotation, new THREE.Quaternion(), t);
        chosen.scale.setScalar(THREE.MathUtils.lerp(fromSize, rect.height / viewport.height * height / 1.5, t));
        const morph = ease((seconds - 1.8) / 1.15);
        const vertices = morphGeometry.attributes.position;
        for (let i = 0; i < vertices.array.length; i++) vertices.array[i] = THREE.MathUtils.lerp(startVertices[i], endVertices[i], morph);
        vertices.needsUpdate = true;
        morphGeometry.computeVertexNormals();
        veinMaterial.opacity = morph * (1 - handoff);
        chosenMaterial.color.set('#ca873c').lerp(new THREE.Color('#2d493e'), ease((seconds - 1.9) / .9));
        // Keep the travelling leaf solid until it has reached the logo.
        // Only then blend into the exact DOM symbol at the same position.
        chosenMaterial.opacity = 1 - handoff;
      }
      renderer.setClearAlpha(0);
      field.material.transparent = true; field.material.opacity = 1 - ease((seconds - 2.4) / .8);
      renderer.render(scene, camera);
      return selected >= 0 && seconds >= 3.15;
    },
    dispose() { veinGroup.children.forEach(mesh => mesh.geometry.dispose()); veinMaterial.dispose(); morphGeometry.dispose(); geometry.dispose(); materials.forEach(m => m.dispose()); chosenMaterial.dispose(); fieldMaterial.dispose(); field.dispose(); scene.clear(); renderer.dispose(); renderer.forceContextLoss(); },
  };
}
