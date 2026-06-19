import { useEffect, useRef } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";

import type { AgentSnapshot, InterpolatedFrame, ReplayEvent, ReplayMetadata } from "../replay/types";
import { getArenaDimensions, simulationToWorld } from "./coordinateTransforms";

export type CameraMode = "angled" | "top" | "free";

interface ArenaSceneProps {
  frame: InterpolatedFrame;
  metadata: ReplayMetadata;
  events: ReplayEvent[];
  selectedAgentId: string | null;
  cameraMode: CameraMode;
  showRanges: boolean;
  showTargets: boolean;
  onSelectAgent: (agentId: string | null) => void;
}

const TEAM_COLORS = [0x35a7ff, 0xff6b35, 0xb785f4, 0xf5d547];

function disposeObject(object: THREE.Object3D): void {
  object.traverse((child) => {
    if (child instanceof THREE.Mesh || child instanceof THREE.Line || child instanceof THREE.Sprite) {
      child.geometry?.dispose();
      const material = child.material;
      const materials = Array.isArray(material) ? material : [material];
      materials.forEach((item) => {
        if (item instanceof THREE.SpriteMaterial && item.map) item.map.dispose();
        item.dispose();
      });
    }
  });
}

function clearGroup(group: THREE.Group): void {
  for (const child of [...group.children]) {
    group.remove(child);
    disposeObject(child);
  }
}

function makeMaterial(color: number, opacity: number): THREE.MeshStandardMaterial {
  return new THREE.MeshStandardMaterial({
    color,
    roughness: 0.52,
    transparent: opacity < 1,
    opacity,
  });
}

function makeTank(color: number, opacity: number): THREE.Group {
  const model = new THREE.Group();
  const chassis = new THREE.Mesh(new THREE.BoxGeometry(2.8, 1.15, 2.15), makeMaterial(color, opacity));
  chassis.position.y = 0.7;
  chassis.castShadow = true;
  model.add(chassis);

  const turret = new THREE.Mesh(
    new THREE.CylinderGeometry(0.7, 0.9, 0.65, 8),
    makeMaterial(0xd6e4f0, opacity),
  );
  turret.position.y = 1.45;
  turret.castShadow = true;
  model.add(turret);

  const barrel = new THREE.Mesh(
    new THREE.CylinderGeometry(0.18, 0.22, 1.8, 8),
    makeMaterial(0x182737, opacity),
  );
  barrel.position.set(0, 1.5, 1.05);
  barrel.rotation.x = Math.PI / 2;
  barrel.castShadow = true;
  model.add(barrel);
  return model;
}

function makeRanged(color: number, opacity: number): THREE.Group {
  const model = new THREE.Group();
  const body = new THREE.Mesh(
    new THREE.CylinderGeometry(0.7, 0.9, 1.7, 8),
    makeMaterial(color, opacity),
  );
  body.position.y = 0.9;
  body.castShadow = true;
  model.add(body);

  const head = new THREE.Mesh(new THREE.IcosahedronGeometry(0.55), makeMaterial(0xe7f5ff, opacity));
  head.position.y = 1.85;
  head.castShadow = true;
  model.add(head);

  const weapon = new THREE.Mesh(
    new THREE.CylinderGeometry(0.14, 0.2, 2.1, 8),
    makeMaterial(0x182737, opacity),
  );
  weapon.position.set(0, 1.15, 1);
  weapon.rotation.x = Math.PI / 2;
  weapon.castShadow = true;
  model.add(weapon);
  return model;
}

function makeSupport(color: number, opacity: number): THREE.Group {
  const model = new THREE.Group();
  const body = new THREE.Mesh(new THREE.OctahedronGeometry(1.15), makeMaterial(color, opacity));
  body.position.y = 1.1;
  body.castShadow = true;
  model.add(body);
  return model;
}

function makeTextSprite(text: string, color: string, scale: [number, number] = [9, 1.7]): THREE.Sprite {
  const canvas = document.createElement("canvas");
  canvas.width = 512;
  canvas.height = 96;
  const context = canvas.getContext("2d");
  if (context) {
    context.fillStyle = "rgba(3, 12, 21, 0.78)";
    context.fillRect(0, 8, canvas.width, 80);
    context.strokeStyle = color;
    context.lineWidth = 4;
    context.strokeRect(2, 10, canvas.width - 4, 76);
    context.fillStyle = "#e9f7ff";
    context.font = "700 34px Segoe UI, sans-serif";
    context.textAlign = "center";
    context.textBaseline = "middle";
    context.fillText(text, canvas.width / 2, canvas.height / 2);
  }
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: texture, transparent: true, depthTest: false }));
  sprite.scale.set(scale[0], scale[1], 1);
  sprite.renderOrder = 20;
  return sprite;
}

function makeHpBar(agent: AgentSnapshot): THREE.Sprite {
  const percentage = Math.max(0, Math.min(1, agent.hp / Math.max(agent.max_hp, 1)));
  const color = percentage > 0.55 ? "#51e3a4" : percentage > 0.25 ? "#ffc857" : "#ff5d73";
  const canvas = document.createElement("canvas");
  canvas.width = 256;
  canvas.height = 32;
  const context = canvas.getContext("2d");
  if (context) {
    context.globalAlpha = agent.alive ? 1 : 0.32;
    context.fillStyle = "#06111c";
    context.fillRect(0, 0, 256, 32);
    context.strokeStyle = "#dceeff";
    context.lineWidth = 3;
    context.strokeRect(1.5, 1.5, 253, 29);
    context.fillStyle = color;
    context.fillRect(7, 7, 242 * percentage, 18);
  }
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: texture, transparent: true, depthTest: false }));
  sprite.position.y = 2.75;
  sprite.scale.set(4.2, 0.52, 1);
  sprite.renderOrder = 19;
  return sprite;
}

function makeLine(
  start: THREE.Vector3,
  end: THREE.Vector3,
  color: number,
  opacity: number,
): THREE.Line {
  const geometry = new THREE.BufferGeometry().setFromPoints([start, end]);
  return new THREE.Line(geometry, new THREE.LineBasicMaterial({ color, transparent: opacity < 1, opacity }));
}

function addAgent(
  parent: THREE.Group,
  agent: AgentSnapshot,
  arena: ReturnType<typeof getArenaDimensions>,
  selected: boolean,
  showRange: boolean,
): void {
  const color = TEAM_COLORS[agent.team_id % TEAM_COLORS.length];
  const opacity = agent.alive ? 1 : 0.28;
  const group = agent.role === "tank"
    ? makeTank(color, opacity)
    : agent.role === "ranged_dps"
      ? makeRanged(color, opacity)
      : makeSupport(color, opacity);
  const world = simulationToWorld(agent.position, arena);
  group.position.set(world[0], agent.alive ? 0 : 0.08, world[2]);
  const facing = agent.facing_vector ?? [0, 1];
  group.rotation.y = Math.atan2(facing[0], facing[1]);
  if (!agent.alive) group.scale.set(1, 0.25, 1);
  group.userData.agentId = agent.agent_id;
  group.traverse((child) => { child.userData.agentId = agent.agent_id; });

  if (showRange && agent.alive && typeof agent.attack_range === "number") {
    const ring = new THREE.Mesh(
      new THREE.RingGeometry(Math.max(0, agent.attack_range - 0.1), agent.attack_range, 80),
      new THREE.MeshBasicMaterial({ color, transparent: true, opacity: selected ? 0.5 : 0.2, side: THREE.DoubleSide }),
    );
    ring.rotation.x = -Math.PI / 2;
    ring.position.y = 0.04;
    group.add(ring);
  }

  if (selected) {
    const ring = new THREE.Mesh(
      new THREE.RingGeometry(1.7, 1.95, 48),
      new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.9, side: THREE.DoubleSide }),
    );
    ring.rotation.x = -Math.PI / 2;
    ring.position.y = 0.06;
    group.add(ring);
  }

  const hpBar = makeHpBar(agent);
  group.add(hpBar);
  const label = makeTextSprite(agent.agent_id, `#${color.toString(16).padStart(6, "0")}`);
  label.position.y = 3.55;
  group.add(label);
  parent.add(group);
}

function addEventEffects(
  parent: THREE.Group,
  events: ReplayEvent[],
  agentsById: Map<string, AgentSnapshot>,
  arena: ReturnType<typeof getArenaDimensions>,
): void {
  for (const event of events) {
    const source = event.source_agent_id ? agentsById.get(event.source_agent_id) : undefined;
    const target = event.target_agent_id ? agentsById.get(event.target_agent_id) : undefined;
    if (event.event_type === "agent_attacked" && source && target) {
      const startPosition = simulationToWorld(source.position, arena);
      const endPosition = simulationToWorld(target.position, arena);
      parent.add(makeLine(
        new THREE.Vector3(startPosition[0], 1.3, startPosition[2]),
        new THREE.Vector3(endPosition[0], 1.3, endPosition[2]),
        0xffd166,
        0.95,
      ));
    } else if (event.event_type === "agent_damaged" && target) {
      const position = simulationToWorld(target.position, arena);
      const damage = typeof event.payload.damage === "number" ? event.payload.damage : "?";
      const sprite = makeTextSprite(`-${damage}`, "#ff6078", [4.4, 1.4]);
      sprite.position.set(position[0], 4.6, position[2]);
      parent.add(sprite);
    } else if (event.event_type === "agent_eliminated" && target) {
      const position = simulationToWorld(target.position, arena);
      const marker = new THREE.Mesh(
        new THREE.RingGeometry(1.3, 2.4, 32),
        new THREE.MeshBasicMaterial({ color: 0xff355e, transparent: true, opacity: 0.85, side: THREE.DoubleSide }),
      );
      marker.rotation.x = -Math.PI / 2;
      marker.position.set(position[0], 0.12, position[2]);
      parent.add(marker);
    }
  }
}

export function ArenaScene({
  frame,
  metadata,
  events,
  selectedAgentId,
  cameraMode,
  showRanges,
  showTargets,
  onSelectAgent,
}: ArenaSceneProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const dynamicGroupRef = useRef<THREE.Group | null>(null);
  const onSelectRef = useRef(onSelectAgent);
  onSelectRef.current = onSelectAgent;

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const arena = getArenaDimensions(metadata);
    const maxDimension = Math.max(arena.width, arena.height);
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x07111f);
    scene.fog = new THREE.Fog(0x07111f, maxDimension * 0.95, maxDimension * 2.2);
    const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 500);
    camera.position.set(maxDimension * 0.62, maxDimension * 0.63, maxDimension * 0.68);
    cameraRef.current = camera;

    const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.75));
    renderer.shadowMap.enabled = true;
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    container.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.minDistance = 12;
    controls.maxDistance = maxDimension * 2.2;
    controls.maxPolarAngle = Math.PI / 2.05;
    controlsRef.current = controls;

    scene.add(new THREE.AmbientLight(0xffffff, 0.7));
    const keyLight = new THREE.DirectionalLight(0xdceeff, 2.1);
    keyLight.position.set(25, 52, 18);
    keyLight.castShadow = true;
    scene.add(keyLight);
    const blueLight = new THREE.PointLight(0x1877ff, 42, 80);
    blueLight.position.set(-35, 18, -20);
    scene.add(blueLight);
    const orangeLight = new THREE.PointLight(0xff5c35, 38, 80);
    orangeLight.position.set(35, 16, 20);
    scene.add(orangeLight);

    const floor = new THREE.Mesh(
      new THREE.PlaneGeometry(arena.width, arena.height),
      new THREE.MeshStandardMaterial({ color: 0x0c1c2c, roughness: 0.92, metalness: 0.08 }),
    );
    floor.rotation.x = -Math.PI / 2;
    floor.position.y = -0.08;
    floor.receiveShadow = true;
    scene.add(floor);
    const grid = new THREE.GridHelper(maxDimension, 20, 0x24516e, 0x173247);
    grid.scale.set(arena.width / maxDimension, 1, arena.height / maxDimension);
    grid.position.y = 0.02;
    scene.add(grid);

    const bounds = [
      new THREE.Vector3(-arena.width / 2, 0.08, -arena.height / 2),
      new THREE.Vector3(arena.width / 2, 0.08, -arena.height / 2),
      new THREE.Vector3(arena.width / 2, 0.08, arena.height / 2),
      new THREE.Vector3(-arena.width / 2, 0.08, arena.height / 2),
      new THREE.Vector3(-arena.width / 2, 0.08, -arena.height / 2),
    ];
    scene.add(new THREE.Line(
      new THREE.BufferGeometry().setFromPoints(bounds),
      new THREE.LineBasicMaterial({ color: 0x6fd8ff, transparent: true, opacity: 0.75 }),
    ));

    for (const obstacle of metadata.config.obstacles ?? []) {
      const center = simulationToWorld(
        [obstacle.x + obstacle.width / 2, obstacle.y + obstacle.height / 2],
        arena,
      );
      const mesh = new THREE.Mesh(
        new THREE.BoxGeometry(obstacle.width, 3, obstacle.height),
        makeMaterial(0x314457, 1),
      );
      mesh.position.set(center[0], 1.5, center[2]);
      mesh.castShadow = true;
      mesh.receiveShadow = true;
      scene.add(mesh);
    }

    const dynamicGroup = new THREE.Group();
    dynamicGroupRef.current = dynamicGroup;
    scene.add(dynamicGroup);

    const resize = () => {
      const width = Math.max(1, container.clientWidth);
      const height = Math.max(1, container.clientHeight);
      renderer.setSize(width, height, false);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
    };
    const resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(container);
    resize();

    const raycaster = new THREE.Raycaster();
    const pointer = new THREE.Vector2();
    const select = (event: PointerEvent) => {
      const rect = renderer.domElement.getBoundingClientRect();
      pointer.set(
        ((event.clientX - rect.left) / rect.width) * 2 - 1,
        -((event.clientY - rect.top) / rect.height) * 2 + 1,
      );
      raycaster.setFromCamera(pointer, camera);
      const hit = raycaster.intersectObjects(dynamicGroup.children, true)
        .find((intersection) => typeof intersection.object.userData.agentId === "string");
      onSelectRef.current(hit?.object.userData.agentId ?? null);
    };
    renderer.domElement.addEventListener("pointerdown", select);

    let animationFrame = 0;
    const render = () => {
      controls.update();
      renderer.render(scene, camera);
      animationFrame = requestAnimationFrame(render);
    };
    render();

    return () => {
      cancelAnimationFrame(animationFrame);
      resizeObserver.disconnect();
      renderer.domElement.removeEventListener("pointerdown", select);
      controls.dispose();
      disposeObject(scene);
      renderer.dispose();
      renderer.domElement.remove();
      cameraRef.current = null;
      controlsRef.current = null;
      dynamicGroupRef.current = null;
    };
  }, [metadata]);

  useEffect(() => {
    const camera = cameraRef.current;
    const controls = controlsRef.current;
    if (!camera || !controls) return;
    const arena = getArenaDimensions(metadata);
    const scale = Math.max(arena.width, arena.height);
    if (cameraMode === "angled") {
      camera.position.set(scale * 0.62, scale * 0.63, scale * 0.68);
      controls.maxPolarAngle = Math.PI / 2.05;
    } else if (cameraMode === "top") {
      camera.position.set(0, scale * 1.08, 0.01);
      controls.maxPolarAngle = 0.15;
    } else {
      controls.maxPolarAngle = Math.PI / 2.05;
    }
    controls.target.set(0, 0, 0);
    controls.update();
  }, [cameraMode, metadata]);

  useEffect(() => {
    const group = dynamicGroupRef.current;
    if (!group) return;
    clearGroup(group);
    const arena = getArenaDimensions(metadata);
    const agentsById = new Map(frame.agents.map((agent) => [agent.agent_id, agent]));
    for (const agent of frame.agents) {
      addAgent(group, agent, arena, selectedAgentId === agent.agent_id, showRanges);
      if (showTargets && agent.alive && agent.current_target_id) {
        const target = agentsById.get(agent.current_target_id);
        if (target?.alive) {
          const start = simulationToWorld(agent.position, arena);
          const end = simulationToWorld(target.position, arena);
          group.add(makeLine(
            new THREE.Vector3(start[0], 0.25, start[2]),
            new THREE.Vector3(end[0], 0.25, end[2]),
            0xffffff,
            0.32,
          ));
        }
      }
    }
    addEventEffects(group, events, agentsById, arena);
  }, [events, frame, metadata, selectedAgentId, showRanges, showTargets]);

  return <div className="three-scene" ref={containerRef} />;
}
