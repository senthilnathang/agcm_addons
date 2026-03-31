<script setup>
/**
 * BIM 3D Viewer — xeokit SDK integration for construction model visualization.
 *
 * Features (Phase 1 MVP):
 * - XKT model loading from backend API
 * - NavCube orientation widget
 * - Object selection with property inspector
 * - Camera modes: orbit, first-person, plan view
 * - Section planes (cross-section cuts)
 * - Distance and angle measurements
 * - X-ray, isolate, show all
 * - BCF viewpoint save
 * - Fit all / fit selected
 */

import { onMounted, onBeforeUnmount, ref, nextTick } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import {
  Viewer,
  XKTLoaderPlugin,
  NavCubePlugin,
  SectionPlanesPlugin,
  DistanceMeasurementsPlugin,
  DistanceMeasurementsMouseControl,
  AngleMeasurementsPlugin,
  AngleMeasurementsMouseControl,
  BCFViewpointsPlugin,
  PointerLens,
} from '@xeokit/xeokit-sdk';

import { Page } from '@vben/common-ui';
import { requestClient } from '#/api/request';

defineOptions({ name: 'AGCMBIMViewer' });

const route = useRoute();
const router = useRouter();
const BASE = '/agcm_bim';

const modelId = ref(route.query.id ? Number(route.query.id) : null);
const modelData = ref(null);
const loading = ref(true);
const loadProgress = ref(0);
const currentTool = ref('select');
const selectedObject = ref(null);
const showProperties = ref(false);
const showSectionOverview = ref(false);

// xeokit instances (module-scoped, not reactive)
let viewer = null;
let xktLoader = null;
let sectionPlanes = null;
let distanceMeasurements = null;
let distanceMeasurementsControl = null;
let angleMeasurements = null;
let angleMeasurementsControl = null;
let bcfViewpoints = null;

// ═══════════════════════════════════════════════════════════
// VIEWER INIT
// ═══════════════════════════════════════════════════════════

async function initViewer() {
  await nextTick();

  // Create Viewer bound to canvas
  viewer = new Viewer({
    canvasId: 'xeokit-canvas',
    transparent: true,
    dtxEnabled: true,
    saoEnabled: true,
    pbrEnabled: false,
    edges: true,
    entityOffsetsEnabled: true,
    pickSurfacePrecisionEnabled: true,
  });

  // Camera defaults
  viewer.camera.eye = [-3.93, 2.85, 27.01];
  viewer.camera.look = [4.40, 3.72, 8.89];
  viewer.camera.up = [-0.01, 0.99, 0.03];
  viewer.cameraControl.navMode = 'orbit';
  viewer.cameraControl.followPointer = true;

  // XKT Loader with IFC defaults
  xktLoader = new XKTLoaderPlugin(viewer, {
    objectDefaults: {
      IfcSpace: { visible: false, pickable: false },
      IfcWindow: { colorize: [0.337, 0.304, 0.871], opacity: 0.3 },
      IfcOpeningElement: { visible: false, pickable: false },
    },
  });

  // NavCube
  new NavCubePlugin(viewer, {
    canvasId: 'navcube-canvas',
    visible: true,
    cameraFly: true,
    cameraFitFOV: 45,
    cameraFlyDuration: 0.5,
  });

  // Section Planes
  sectionPlanes = new SectionPlanesPlugin(viewer, {
    overviewCanvasId: 'section-overview-canvas',
    overviewVisible: true,
  });

  // Distance Measurements
  distanceMeasurements = new DistanceMeasurementsPlugin(viewer, {
    defaultLabelsVisible: true, defaultAxisVisible: true, defaultColor: '#00BBFF',
  });
  distanceMeasurementsControl = new DistanceMeasurementsMouseControl(distanceMeasurements, {
    pointerLens: new PointerLens(viewer), snapToVertex: true, snapToEdge: true,
  });

  // Angle Measurements
  angleMeasurements = new AngleMeasurementsPlugin(viewer, {
    defaultColor: '#FF4444', defaultLabelsVisible: true,
  });
  angleMeasurementsControl = new AngleMeasurementsMouseControl(angleMeasurements, {
    pointerLens: new PointerLens(viewer), snapToVertex: true, snapToEdge: true,
  });

  // BCF Viewpoints
  bcfViewpoints = new BCFViewpointsPlugin(viewer, {
    originatingSystem: 'FastVue BuildForge',
    authoringTool: 'BuildForge BIM Viewer v1.0',
  });

  // Object picking
  viewer.cameraControl.on('picked', (pickResult) => {
    if (!pickResult || !pickResult.entity) { selectedObject.value = null; showProperties.value = false; return; }
    const entity = pickResult.entity;
    const metaObject = viewer.metaScene.metaObjects[entity.id];
    entity.selected = !entity.selected;
    selectedObject.value = {
      entityId: entity.id,
      name: metaObject?.name || entity.id,
      type: metaObject?.type || 'Unknown',
      properties: metaObject?.propertySetDicts || {},
    };
    showProperties.value = true;
  });

  viewer.cameraControl.on('pickedNothing', () => {
    viewer.scene.setObjectsSelected(viewer.scene.selectedObjectIds, false);
    selectedObject.value = null;
    showProperties.value = false;
  });

  // Resize handler
  const container = document.querySelector('.bim-viewer-container');
  if (container) {
    new ResizeObserver(() => viewer?.scene?.canvas?.resizeCanvas?.()).observe(container);
  }

  // Load model
  if (modelId.value) await loadModel(modelId.value);
  else loading.value = false;
}

// ═══════════════════════════════════════════════════════════
// MODEL LOADING
// ═══════════════════════════════════════════════════════════

async function loadModel(id) {
  loading.value = true;
  loadProgress.value = 10;
  try {
    const data = await requestClient.get(`${BASE}/models/${id}`);
    modelData.value = data;
    loadProgress.value = 30;

    const sceneModel = xktLoader.load({
      id: `model-${id}`,
      src: `/api/v1${BASE}/models/${id}/xkt`,
      edges: true, saoEnabled: true, dtxEnabled: true,
      rotation: [data.rotation_x || 0, data.rotation_y || 0, data.rotation_z || 0],
      scale: [data.scale_factor || 1, data.scale_factor || 1, data.scale_factor || 1],
      position: [data.position_x || 0, data.position_y || 0, data.position_z || 0],
      excludeTypes: ['IfcSpace', 'IfcOpeningElement'],
    });
    loadProgress.value = 60;

    sceneModel.on('loaded', () => {
      loadProgress.value = 100;
      loading.value = false;
      viewer.cameraFlight.flyTo({ aabb: sceneModel.aabb, duration: 1 });
    });
    sceneModel.on('error', (err) => { loading.value = false; console.error('XKT load error:', err); });
  } catch (e) {
    loading.value = false;
    console.error('Model load failed:', e);
  }
}

// ═══════════════════════════════════════════════════════════
// TOOL SWITCHING
// ═══════════════════════════════════════════════════════════

function setTool(tool) {
  distanceMeasurementsControl?.deactivate();
  angleMeasurementsControl?.deactivate();
  sectionPlanes?.hideControl();

  switch (tool) {
    case 'orbit': viewer.cameraControl.navMode = 'orbit'; break;
    case 'firstPerson': viewer.cameraControl.navMode = 'firstPerson'; break;
    case 'planView': viewer.cameraControl.navMode = 'planView'; break;
    case 'measureDistance': distanceMeasurementsControl.activate(); break;
    case 'measureAngle': angleMeasurementsControl.activate(); break;
    case 'section':
      sectionPlanes.createSectionPlane({ pos: viewer.camera.look.slice(), dir: [0, -1, 0], active: true });
      showSectionOverview.value = true;
      break;
    case 'xray':
      viewer.scene.setObjectsXRayed(viewer.scene.objectIds, true);
      if (viewer.scene.selectedObjectIds.length) viewer.scene.setObjectsXRayed(viewer.scene.selectedObjectIds, false);
      break;
    case 'isolate':
      if (selectedObject.value) {
        const ids = viewer.metaScene.getObjectIDsInSubtree(selectedObject.value.entityId);
        viewer.scene.setObjectsVisible(viewer.scene.objectIds, false);
        viewer.scene.setObjectsVisible(ids, true);
        viewer.cameraFlight.flyTo({ aabb: viewer.scene.getAABB(ids), duration: 0.5 });
      }
      break;
    case 'showAll':
      viewer.scene.setObjectsVisible(viewer.scene.objectIds, true);
      viewer.scene.setObjectsXRayed(viewer.scene.objectIds, false);
      viewer.scene.setObjectsSelected(viewer.scene.objectIds, false);
      break;
    case 'fitAll':
      viewer.cameraFlight.flyTo({ aabb: viewer.scene.aabb, duration: 0.5 });
      break;
  }
  currentTool.value = tool;
}

async function saveViewpoint() {
  if (!bcfViewpoints) return;
  const vp = bcfViewpoints.getViewpoint({ spacesVisible: false, openingsVisible: false, snapshot: true, defaultInvisible: true });
  try {
    await requestClient.post(`${BASE}/viewpoints`, {
      model_id: modelId.value,
      name: `Viewpoint ${new Date().toLocaleString()}`,
      camera_position: JSON.stringify(vp.perspective_camera || vp.orthographic_camera || {}),
      camera_target: JSON.stringify({ x: viewer.camera.look[0], y: viewer.camera.look[1], z: viewer.camera.look[2] }),
      annotations: JSON.stringify(vp),
    });
  } catch (e) { console.error('Save viewpoint failed:', e); }
}

function clearMeasurements() { distanceMeasurements?.clear(); angleMeasurements?.clear(); }
function clearSections() { sectionPlanes?.clear(); showSectionOverview.value = false; }

// ═══════════════════════════════════════════════════════════
// LIFECYCLE
// ═══════════════════════════════════════════════════════════

onMounted(() => initViewer());
onBeforeUnmount(() => { if (viewer) { viewer.destroy(); viewer = null; } });
</script>

<template>
  <Page title="BIM 3D Viewer" description="Interactive 3D model viewer powered by xeokit">
    <div class="bim-page">
      <!-- Toolbar -->
      <div class="bim-toolbar">
        <ASpace wrap>
          <AButton size="small" @click="router.push('/agcm/bim/models')">Back</AButton>
          <ADivider type="vertical" />
          <ATooltip title="Orbit"><AButton size="small" :type="currentTool==='orbit'?'primary':'default'" @click="setTool('orbit')">Orbit</AButton></ATooltip>
          <ATooltip title="Walk"><AButton size="small" :type="currentTool==='firstPerson'?'primary':'default'" @click="setTool('firstPerson')">Walk</AButton></ATooltip>
          <ATooltip title="Plan"><AButton size="small" :type="currentTool==='planView'?'primary':'default'" @click="setTool('planView')">Plan</AButton></ATooltip>
          <ADivider type="vertical" />
          <ATooltip title="Distance"><AButton size="small" :type="currentTool==='measureDistance'?'primary':'default'" @click="setTool('measureDistance')">Distance</AButton></ATooltip>
          <ATooltip title="Angle"><AButton size="small" :type="currentTool==='measureAngle'?'primary':'default'" @click="setTool('measureAngle')">Angle</AButton></ATooltip>
          <ATooltip title="Section Cut"><AButton size="small" @click="setTool('section')">Section</AButton></ATooltip>
          <ADivider type="vertical" />
          <AButton size="small" @click="setTool('xray')">X-Ray</AButton>
          <AButton size="small" @click="setTool('isolate')">Isolate</AButton>
          <AButton size="small" @click="setTool('showAll')">Show All</AButton>
          <AButton size="small" @click="setTool('fitAll')">Fit</AButton>
          <ADivider type="vertical" />
          <AButton size="small" @click="saveViewpoint">Save View</AButton>
          <AButton size="small" @click="clearMeasurements">Clear Measures</AButton>
          <AButton size="small" @click="clearSections">Clear Sections</AButton>
        </ASpace>
      </div>

      <!-- Viewer -->
      <div class="bim-viewer-container">
        <canvas id="xeokit-canvas" class="bim-canvas" />
        <canvas id="navcube-canvas" class="navcube-canvas" />
        <canvas id="section-overview-canvas" class="section-canvas" v-show="showSectionOverview" />

        <!-- Loading -->
        <div v-if="loading" class="bim-loading">
          <ASpin size="large" />
          <div style="margin-top:12px;font-size:13px;color:#555;">Loading model... {{ loadProgress }}%</div>
          <AProgress :percent="loadProgress" :show-info="false" style="width:200px;margin-top:8px;" />
        </div>

        <!-- Properties -->
        <div v-if="showProperties && selectedObject" class="bim-props">
          <div class="bim-props-head"><strong>{{ selectedObject.name }}</strong><AButton type="text" size="small" @click="showProperties=false">X</AButton></div>
          <div class="bim-props-body">
            <div class="prop-r"><span class="prop-l">Entity ID</span><span class="prop-v" style="font-family:monospace;">{{ selectedObject.entityId }}</span></div>
            <div class="prop-r"><span class="prop-l">IFC Type</span><ATag color="blue" size="small">{{ selectedObject.type }}</ATag></div>
            <template v-if="selectedObject.properties">
              <template v-for="(propSet, setName) in selectedObject.properties" :key="setName">
                <div style="font-size:10px;font-weight:600;color:#555;margin-top:6px;border-top:1px solid #f0f0f0;padding-top:4px;">{{ setName }}</div>
                <div v-for="(val, key) in propSet" :key="key" class="prop-r"><span class="prop-l">{{ key }}</span><span class="prop-v">{{ val }}</span></div>
              </template>
            </template>
          </div>
        </div>

        <!-- Model info badge -->
        <div v-if="modelData" class="bim-info">
          <strong>{{ modelData.name }}</strong>
          <span style="color:#999;font-size:10px;margin-left:6px;">.{{ modelData.file_format }}</span>
          <ATag :color="modelData.status==='ready'?'green':'orange'" size="small" style="margin-left:6px;">{{ modelData.status }}</ATag>
        </div>
      </div>
    </div>
  </Page>
</template>

<style scoped>
.bim-page { display: flex; flex-direction: column; height: calc(100vh - 120px); }
.bim-toolbar { padding: 6px 12px; background: #fafafa; border-bottom: 1px solid #e8e8e8; flex-shrink: 0; overflow-x: auto; }
.bim-viewer-container { position: relative; flex: 1; overflow: hidden; background: linear-gradient(135deg, #e8edf2, #f5f5f5, #ffffff); }
.bim-canvas { width: 100%; height: 100%; display: block; }
.navcube-canvas { position: absolute; top: 12px; right: 12px; width: 150px; height: 150px; z-index: 10; }
.section-canvas { position: absolute; bottom: 12px; right: 12px; width: 200px; height: 200px; z-index: 10; border: 1px solid #ccc; border-radius: 6px; background: #fff; }
.bim-loading { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; background: rgba(255,255,255,0.88); z-index: 20; }
.bim-props { position: absolute; top: 12px; right: 170px; width: 280px; max-height: calc(100% - 24px); background: #fff; border: 1px solid #e0e0e0; border-radius: 6px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); z-index: 15; overflow-y: auto; }
.bim-props-head { display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; border-bottom: 1px solid #f0f0f0; background: #fafafa; font-size: 12px; }
.bim-props-body { padding: 8px 12px; font-size: 11px; }
.prop-r { display: flex; justify-content: space-between; padding: 2px 0; border-bottom: 1px solid #f8f8f8; }
.prop-l { color: #888; font-size: 10px; }
.prop-v { color: #333; font-size: 10px; max-width: 160px; word-break: break-all; }
.bim-info { position: absolute; top: 12px; left: 12px; background: rgba(255,255,255,0.92); border: 1px solid #e0e0e0; border-radius: 6px; padding: 6px 12px; z-index: 15; font-size: 12px; display: flex; align-items: center; }
</style>
