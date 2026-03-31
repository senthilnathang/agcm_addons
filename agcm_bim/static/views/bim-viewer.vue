<script setup>
/**
 * BIM 3D Viewer — Phase 2: Full BIM Tools
 *
 * Features:
 * - XKT model loading with multi-model federation
 * - IFC Tree Panel (spatial hierarchy browser)
 * - Section Planes Panel with interactive controls
 * - Measurement Panel (distance + angle listing)
 * - 3D Annotations with backend persistence
 * - Enhanced toolbar with grouped tools
 * - Keyboard shortcuts
 * - NavCube, BCF viewpoints, object selection
 */

import { onMounted, onBeforeUnmount, ref, reactive, computed, nextTick, watch } from 'vue';
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
  TreeViewPlugin,
  AnnotationsPlugin,
  PointerLens,
} from '@xeokit/xeokit-sdk';

import { Page } from '@vben/common-ui';
import { requestClient } from '#/api/request';

defineOptions({ name: 'AGCMBIMViewer' });

const route = useRoute();
const router = useRouter();
const BASE = '/agcm_bim';

// ═══════════════════════════════════════════════════════════
// STATE
// ═══════════════════════════════════════════════════════════

const modelId = ref(route.query.id ? Number(route.query.id) : null);
const projectId = ref(route.query.project_id ? Number(route.query.project_id) : null);
const modelData = ref(null);
const loading = ref(true);
const loadProgress = ref(0);
const currentTool = ref('select');
const selectedObject = ref(null);
const showProperties = ref(false);
const showSectionOverview = ref(false);

// IFC Tree
const showTreePanel = ref(false);

// Section Planes Panel
const showSectionPanel = ref(false);
const sectionPlanesList = ref([]);

// Measurement Panel
const showMeasurementPanel = ref(false);
const distanceMeasurementsList = ref([]);
const angleMeasurementsList = ref([]);

// Annotations
const showAnnotationPanel = ref(false);
const annotationsList = ref([]);
const annotationDrawerVisible = ref(false);
const annotationForm = reactive({
  title: '',
  description: '',
  priority: 'medium',
  world_pos_x: 0,
  world_pos_y: 0,
  world_pos_z: 0,
  entity_id: null,
});
const annotationsVisible = ref(true);
const savingAnnotation = ref(false);

// Multi-Model
const showModelListPanel = ref(false);
const loadModelModalVisible = ref(false);
const availableModels = ref([]);
const loadedModels = ref([]);
const loadingAdditionalModel = ref(false);

// xeokit instances (module-scoped, not reactive)
let viewer = null;
let xktLoader = null;
let sectionPlanesPlugin = null;
let distanceMeasurements = null;
let distanceMeasurementsControl = null;
let angleMeasurements = null;
let angleMeasurementsControl = null;
let bcfViewpoints = null;
let treeViewPlugin = null;
let annotationsPlugin = null;

// ═══════════════════════════════════════════════════════════
// VIEWER INIT
// ═══════════════════════════════════════════════════════════

async function initViewer() {
  await nextTick();

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

  // XKT Loader
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
  sectionPlanesPlugin = new SectionPlanesPlugin(viewer, {
    overviewCanvasId: 'section-overview-canvas',
    overviewVisible: true,
  });

  // Distance Measurements
  distanceMeasurements = new DistanceMeasurementsPlugin(viewer, {
    defaultLabelsVisible: true,
    defaultAxisVisible: true,
    defaultColor: '#00BBFF',
  });
  distanceMeasurementsControl = new DistanceMeasurementsMouseControl(distanceMeasurements, {
    pointerLens: new PointerLens(viewer),
    snapToVertex: true,
    snapToEdge: true,
  });

  // Angle Measurements
  angleMeasurements = new AngleMeasurementsPlugin(viewer, {
    defaultColor: '#FF4444',
    defaultLabelsVisible: true,
  });
  angleMeasurementsControl = new AngleMeasurementsMouseControl(angleMeasurements, {
    pointerLens: new PointerLens(viewer),
    snapToVertex: true,
    snapToEdge: true,
  });

  // BCF Viewpoints
  bcfViewpoints = new BCFViewpointsPlugin(viewer, {
    originatingSystem: 'FastVue BuildForge',
    authoringTool: 'BuildForge BIM Viewer v2.0',
  });

  // IFC Tree
  treeViewPlugin = new TreeViewPlugin(viewer, {
    containerElement: document.getElementById('bim-tree-container'),
    hierarchy: 'containment',
    autoExpandDepth: 1,
  });

  // Annotations Plugin
  annotationsPlugin = new AnnotationsPlugin(viewer, {
    markerHTML: '<div class="bim-annotation-marker">{{glyph}}</div>',
    labelHTML: '<div class="bim-annotation-label"><b>{{title}}</b><p>{{description}}</p></div>',
  });

  // Object picking
  viewer.cameraControl.on('picked', (pickResult) => {
    if (!pickResult || !pickResult.entity) {
      selectedObject.value = null;
      showProperties.value = false;
      return;
    }
    const entity = pickResult.entity;
    const metaObject = viewer.metaScene.metaObjects[entity.id];

    // In annotation mode, create annotation at pick point
    if (currentTool.value === 'annotate' && pickResult.worldPos) {
      openAnnotationDrawer(pickResult);
      return;
    }

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
    if (currentTool.value !== 'annotate') {
      viewer.scene.setObjectsSelected(viewer.scene.selectedObjectIds, false);
      selectedObject.value = null;
      showProperties.value = false;
    }
  });

  // Resize handler
  const container = document.querySelector('.bim-viewer-container');
  if (container) {
    new ResizeObserver(() => viewer?.scene?.canvas?.resizeCanvas?.()).observe(container);
  }

  // Keyboard shortcuts
  document.addEventListener('keydown', handleKeyDown);

  // Load model
  if (modelId.value) {
    await loadModel(modelId.value);
  } else {
    loading.value = false;
  }
}

// ═══════════════════════════════════════════════════════════
// MODEL LOADING
// ═══════════════════════════════════════════════════════════

async function loadModel(id, federation) {
  loading.value = true;
  loadProgress.value = 10;
  try {
    const data = await requestClient.get(`${BASE}/models/${id}`);
    if (!federation) {
      modelData.value = data;
      projectId.value = data.project_id;
    }
    loadProgress.value = 30;

    const sceneModelId = `model-${id}`;
    const transforms = federation || {};

    const sceneModel = xktLoader.load({
      id: sceneModelId,
      src: `/api/v1${BASE}/models/${id}/xkt`,
      edges: true,
      saoEnabled: true,
      dtxEnabled: true,
      rotation: [
        transforms.rotation_x ?? data.rotation_x ?? 0,
        transforms.rotation_y ?? data.rotation_y ?? 0,
        transforms.rotation_z ?? data.rotation_z ?? 0,
      ],
      scale: [
        transforms.scale ?? data.scale_factor ?? 1,
        transforms.scale ?? data.scale_factor ?? 1,
        transforms.scale ?? data.scale_factor ?? 1,
      ],
      position: [
        transforms.position_x ?? data.position_x ?? 0,
        transforms.position_y ?? data.position_y ?? 0,
        transforms.position_z ?? data.position_z ?? 0,
      ],
      excludeTypes: ['IfcSpace', 'IfcOpeningElement'],
    });
    loadProgress.value = 60;

    sceneModel.on('loaded', () => {
      loadProgress.value = 100;
      loading.value = false;
      loadingAdditionalModel.value = false;
      viewer.cameraFlight.flyTo({ aabb: viewer.scene.aabb, duration: 1 });

      // Track loaded model
      const entry = {
        id: id,
        sceneModelId: sceneModelId,
        name: data.name,
        discipline: data.discipline,
        format: data.file_format,
        visible: true,
      };
      if (!loadedModels.value.find((m) => m.id === id)) {
        loadedModels.value.push(entry);
      }

      // Refresh tree
      refreshTree();

      // Load annotations for project
      if (projectId.value) {
        loadAnnotations();
      }

      refreshMeasurementsList();
      refreshSectionPlanesList();
    });

    sceneModel.on('error', (err) => {
      loading.value = false;
      loadingAdditionalModel.value = false;
      console.error('XKT load error:', err);
    });
  } catch (e) {
    loading.value = false;
    loadingAdditionalModel.value = false;
    console.error('Model load failed:', e);
  }
}

function unloadModel(entry) {
  const sceneModel = viewer.scene.models[entry.sceneModelId];
  if (sceneModel) {
    sceneModel.destroy();
  }
  loadedModels.value = loadedModels.value.filter((m) => m.id !== entry.id);
  refreshTree();
}

function toggleModelVisibility(entry) {
  const sceneModel = viewer.scene.models[entry.sceneModelId];
  if (sceneModel) {
    entry.visible = !entry.visible;
    const objectIds = sceneModel.objectIds || [];
    viewer.scene.setObjectsVisible(objectIds, entry.visible);
  }
}

// ═══════════════════════════════════════════════════════════
// MULTI-MODEL FEDERATION
// ═══════════════════════════════════════════════════════════

async function openLoadModelModal() {
  if (!projectId.value) return;
  try {
    const result = await requestClient.get(`${BASE}/models`, {
      params: { project_id: projectId.value, status: 'ready', page_size: 100 },
    });
    availableModels.value = (result.items || result || []).filter(
      (m) => !loadedModels.value.find((lm) => lm.id === m.id)
    );
    loadModelModalVisible.value = true;
  } catch (e) {
    console.error('Failed to fetch models:', e);
  }
}

async function loadAdditionalModel(model) {
  loadModelModalVisible.value = false;
  loadingAdditionalModel.value = true;
  await loadModel(model.id, {
    position_x: model.position_x || 0,
    position_y: model.position_y || 0,
    position_z: model.position_z || 0,
    rotation_x: model.rotation_x || 0,
    rotation_y: model.rotation_y || 0,
    rotation_z: model.rotation_z || 0,
    scale: model.scale_factor || 1,
  });
}

// ═══════════════════════════════════════════════════════════
// IFC TREE
// ═══════════════════════════════════════════════════════════

function refreshTree() {
  // TreeViewPlugin auto-rebuilds when models are added/removed
  // Just ensure the container is visible
}

function toggleTreePanel() {
  showTreePanel.value = !showTreePanel.value;
  // Force canvas resize after sidebar toggle
  nextTick(() => viewer?.scene?.canvas?.resizeCanvas?.());
}

// Tree node context menu actions
function treeIsolate(nodeId) {
  const ids = viewer.metaScene.getObjectIDsInSubtree(nodeId);
  if (ids.length) {
    viewer.scene.setObjectsVisible(viewer.scene.objectIds, false);
    viewer.scene.setObjectsVisible(ids, true);
    viewer.cameraFlight.flyTo({ aabb: viewer.scene.getAABB(ids), duration: 0.5 });
  }
}

function treeHide(nodeId) {
  const ids = viewer.metaScene.getObjectIDsInSubtree(nodeId);
  viewer.scene.setObjectsVisible(ids, false);
}

function treeXRay(nodeId) {
  const ids = viewer.metaScene.getObjectIDsInSubtree(nodeId);
  viewer.scene.setObjectsXRayed(ids, true);
}

function treeFlyTo(nodeId) {
  const ids = viewer.metaScene.getObjectIDsInSubtree(nodeId);
  if (ids.length) {
    viewer.cameraFlight.flyTo({ aabb: viewer.scene.getAABB(ids), duration: 0.5 });
  }
}

// ═══════════════════════════════════════════════════════════
// SECTION PLANES
// ═══════════════════════════════════════════════════════════

function refreshSectionPlanesList() {
  if (!sectionPlanesPlugin) return;
  const planes = [];
  const spMap = sectionPlanesPlugin.sectionPlanes;
  for (const id in spMap) {
    const sp = spMap[id];
    planes.push({
      id: id,
      active: sp.active,
      pos: sp.pos.slice(),
      dir: sp.dir.slice(),
    });
  }
  sectionPlanesList.value = planes;
}

function flipSectionPlane(planeId) {
  const sp = sectionPlanesPlugin.sectionPlanes[planeId];
  if (sp) {
    sp.dir = [-sp.dir[0], -sp.dir[1], -sp.dir[2]];
    refreshSectionPlanesList();
  }
}

function toggleSectionPlaneActive(planeId) {
  const sp = sectionPlanesPlugin.sectionPlanes[planeId];
  if (sp) {
    sp.active = !sp.active;
    refreshSectionPlanesList();
  }
}

function deleteSectionPlane(planeId) {
  const sp = sectionPlanesPlugin.sectionPlanes[planeId];
  if (sp) {
    sp.destroy();
    refreshSectionPlanesList();
  }
}

function editSectionPlane(planeId) {
  sectionPlanesPlugin.showControl(planeId);
}

function flipAllSectionPlanes() {
  const spMap = sectionPlanesPlugin.sectionPlanes;
  for (const id in spMap) {
    const sp = spMap[id];
    sp.dir = [-sp.dir[0], -sp.dir[1], -sp.dir[2]];
  }
  refreshSectionPlanesList();
}

// ═══════════════════════════════════════════════════════════
// MEASUREMENTS
// ═══════════════════════════════════════════════════════════

function refreshMeasurementsList() {
  // Distance measurements
  const dList = [];
  if (distanceMeasurements) {
    const measurements = distanceMeasurements.measurements;
    for (const id in measurements) {
      const m = measurements[id];
      dList.push({
        id: id,
        length: m.length != null ? m.length.toFixed(3) : '?',
      });
    }
  }
  distanceMeasurementsList.value = dList;

  // Angle measurements
  const aList = [];
  if (angleMeasurements) {
    const measurements = angleMeasurements.measurements;
    for (const id in measurements) {
      const m = measurements[id];
      aList.push({
        id: id,
        angle: m.angle != null ? m.angle.toFixed(1) : '?',
      });
    }
  }
  angleMeasurementsList.value = aList;
}

function deleteDistanceMeasurement(id) {
  const m = distanceMeasurements.measurements[id];
  if (m) m.destroy();
  refreshMeasurementsList();
}

function deleteAngleMeasurement(id) {
  const m = angleMeasurements.measurements[id];
  if (m) m.destroy();
  refreshMeasurementsList();
}

// ═══════════════════════════════════════════════════════════
// ANNOTATIONS
// ═══════════════════════════════════════════════════════════

async function loadAnnotations() {
  if (!projectId.value) return;
  try {
    const params = { project_id: projectId.value };
    if (modelId.value) params.model_id = modelId.value;
    const items = await requestClient.get(`${BASE}/annotations`, { params });
    annotationsList.value = items || [];
    renderAnnotationMarkers();
  } catch (e) {
    console.error('Failed to load annotations:', e);
  }
}

function renderAnnotationMarkers() {
  if (!annotationsPlugin) return;
  // Clear existing plugin annotations
  annotationsPlugin.clear();

  annotationsList.value.forEach((ann, idx) => {
    const markerId = `ann-${ann.id}`;
    try {
      annotationsPlugin.createAnnotation({
        id: markerId,
        worldPos: [ann.world_pos_x, ann.world_pos_y, ann.world_pos_z],
        occludable: true,
        markerShown: annotationsVisible.value,
        labelShown: false,
        values: {
          glyph: String(idx + 1),
          title: ann.title || '',
          description: ann.description || '',
        },
      });
    } catch (e) {
      // Annotation may already exist
    }
  });
}

function openAnnotationDrawer(pickResult) {
  annotationForm.title = '';
  annotationForm.description = '';
  annotationForm.priority = 'medium';
  annotationForm.world_pos_x = pickResult.worldPos[0];
  annotationForm.world_pos_y = pickResult.worldPos[1];
  annotationForm.world_pos_z = pickResult.worldPos[2];
  annotationForm.entity_id = pickResult.entity?.id || null;
  annotationDrawerVisible.value = true;
}

async function saveAnnotation() {
  if (!annotationForm.title.trim()) return;
  savingAnnotation.value = true;
  try {
    const cam = viewer.camera;
    const payload = {
      project_id: projectId.value || modelData.value?.project_id,
      model_id: modelId.value,
      world_pos_x: annotationForm.world_pos_x,
      world_pos_y: annotationForm.world_pos_y,
      world_pos_z: annotationForm.world_pos_z,
      eye_x: cam.eye[0],
      eye_y: cam.eye[1],
      eye_z: cam.eye[2],
      look_x: cam.look[0],
      look_y: cam.look[1],
      look_z: cam.look[2],
      up_x: cam.up[0],
      up_y: cam.up[1],
      up_z: cam.up[2],
      entity_id: annotationForm.entity_id,
      title: annotationForm.title,
      description: annotationForm.description,
      priority: annotationForm.priority,
    };
    await requestClient.post(`${BASE}/annotations`, payload);
    annotationDrawerVisible.value = false;
    await loadAnnotations();
  } catch (e) {
    console.error('Failed to save annotation:', e);
  } finally {
    savingAnnotation.value = false;
  }
}

async function deleteAnnotation(ann) {
  try {
    await requestClient.delete(`${BASE}/annotations/${ann.id}`);
    await loadAnnotations();
  } catch (e) {
    console.error('Failed to delete annotation:', e);
  }
}

async function resolveAnnotation(ann) {
  try {
    await requestClient.post(`${BASE}/annotations/${ann.id}/resolve`);
    await loadAnnotations();
  } catch (e) {
    console.error('Failed to resolve annotation:', e);
  }
}

function flyToAnnotation(ann) {
  if (ann.eye_x != null && ann.look_x != null) {
    viewer.cameraFlight.flyTo({
      eye: [ann.eye_x, ann.eye_y, ann.eye_z],
      look: [ann.look_x, ann.look_y, ann.look_z],
      up: [ann.up_x || 0, ann.up_y || 1, ann.up_z || 0],
      duration: 0.5,
    });
  } else {
    viewer.cameraFlight.flyTo({
      aabb: [
        ann.world_pos_x - 2, ann.world_pos_y - 2, ann.world_pos_z - 2,
        ann.world_pos_x + 2, ann.world_pos_y + 2, ann.world_pos_z + 2,
      ],
      duration: 0.5,
    });
  }
}

function toggleAnnotationsVisible() {
  annotationsVisible.value = !annotationsVisible.value;
  if (annotationsPlugin) {
    const anns = annotationsPlugin.annotations;
    for (const id in anns) {
      anns[id].markerShown = annotationsVisible.value;
    }
  }
}

// ═══════════════════════════════════════════════════════════
// TOOL SWITCHING
// ═══════════════════════════════════════════════════════════

function setTool(tool) {
  distanceMeasurementsControl?.deactivate();
  angleMeasurementsControl?.deactivate();
  sectionPlanesPlugin?.hideControl();

  switch (tool) {
    case 'select':
      // Default mode: do nothing special
      break;
    case 'orbit':
      viewer.cameraControl.navMode = 'orbit';
      break;
    case 'firstPerson':
      viewer.cameraControl.navMode = 'firstPerson';
      break;
    case 'planView':
      viewer.cameraControl.navMode = 'planView';
      break;
    case 'measureDistance':
      distanceMeasurementsControl.activate();
      showMeasurementPanel.value = true;
      break;
    case 'measureAngle':
      angleMeasurementsControl.activate();
      showMeasurementPanel.value = true;
      break;
    case 'section':
      sectionPlanesPlugin.createSectionPlane({
        pos: viewer.camera.look.slice(),
        dir: [0, -1, 0],
        active: true,
      });
      showSectionOverview.value = true;
      showSectionPanel.value = true;
      refreshSectionPlanesList();
      break;
    case 'xray':
      viewer.scene.setObjectsXRayed(viewer.scene.objectIds, true);
      if (viewer.scene.selectedObjectIds.length) {
        viewer.scene.setObjectsXRayed(viewer.scene.selectedObjectIds, false);
      }
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
    case 'annotate':
      // Handled in the picked event
      break;
  }
  currentTool.value = tool;

  // Refresh measurement list when switching tools
  refreshMeasurementsList();
}

async function saveViewpoint() {
  if (!bcfViewpoints) return;
  const vp = bcfViewpoints.getViewpoint({
    spacesVisible: false,
    openingsVisible: false,
    snapshot: true,
    defaultInvisible: true,
  });
  try {
    await requestClient.post(`${BASE}/viewpoints`, {
      model_id: modelId.value,
      name: `Viewpoint ${new Date().toLocaleString()}`,
      camera_position: JSON.stringify(vp.perspective_camera || vp.orthographic_camera || {}),
      camera_target: JSON.stringify({
        x: viewer.camera.look[0],
        y: viewer.camera.look[1],
        z: viewer.camera.look[2],
      }),
      annotations: JSON.stringify(vp),
    });
  } catch (e) {
    console.error('Save viewpoint failed:', e);
  }
}

function clearMeasurements() {
  distanceMeasurements?.clear();
  angleMeasurements?.clear();
  refreshMeasurementsList();
}

function clearSections() {
  sectionPlanesPlugin?.clear();
  showSectionOverview.value = false;
  refreshSectionPlanesList();
}

// ═══════════════════════════════════════════════════════════
// KEYBOARD SHORTCUTS
// ═══════════════════════════════════════════════════════════

function handleKeyDown(e) {
  // Don't intercept when typing in input fields
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.isContentEditable) {
    return;
  }

  switch (e.key) {
    case 'Escape':
      setTool('select');
      annotationDrawerVisible.value = false;
      break;
    case 'f':
    case 'F':
      if (!e.ctrlKey && !e.metaKey) {
        e.preventDefault();
        setTool('fitAll');
      }
      break;
    case 'h':
    case 'H':
      if (!e.ctrlKey && !e.metaKey) {
        e.preventDefault();
        if (selectedObject.value) {
          viewer.scene.setObjectsVisible([selectedObject.value.entityId], false);
        }
      }
      break;
    case 'x':
    case 'X':
      if (!e.ctrlKey && !e.metaKey) {
        e.preventDefault();
        if (selectedObject.value) {
          viewer.scene.setObjectsXRayed([selectedObject.value.entityId], true);
        }
      }
      break;
    case 'Delete':
      // Delete selected measurement or section
      break;
  }
}

// ═══════════════════════════════════════════════════════════
// HELPERS
// ═══════════════════════════════════════════════════════════

const priorityColors = { low: 'blue', medium: 'orange', high: 'red', critical: 'magenta' };
const statusColors = { open: 'orange', in_progress: 'blue', resolved: 'green' };

function formatDir(dir) {
  return `[${dir.map((v) => v.toFixed(2)).join(', ')}]`;
}

// ═══════════════════════════════════════════════════════════
// LIFECYCLE
// ═══════════════════════════════════════════════════════════

onMounted(() => initViewer());

onBeforeUnmount(() => {
  document.removeEventListener('keydown', handleKeyDown);
  if (viewer) {
    viewer.destroy();
    viewer = null;
  }
});
</script>

<template>
  <Page title="BIM 3D Viewer" description="Interactive 3D model viewer powered by xeokit">
    <div class="bim-page">
      <!-- ═══════════ TOOLBAR ═══════════ -->
      <div class="bim-toolbar">
        <div class="bim-toolbar-inner">
          <AButton size="small" @click="router.push('/agcm/bim/models')">Back</AButton>
          <ADivider type="vertical" />

          <!-- Navigation Group -->
          <AButtonGroup size="small">
            <ATooltip title="Orbit (camera)">
              <AButton :type="currentTool === 'orbit' ? 'primary' : 'default'" @click="setTool('orbit')">Orbit</AButton>
            </ATooltip>
            <ATooltip title="Walk (first person)">
              <AButton :type="currentTool === 'firstPerson' ? 'primary' : 'default'" @click="setTool('firstPerson')">Walk</AButton>
            </ATooltip>
            <ATooltip title="Plan view (top down)">
              <AButton :type="currentTool === 'planView' ? 'primary' : 'default'" @click="setTool('planView')">Plan</AButton>
            </ATooltip>
            <ATooltip title="Fit all (F)">
              <AButton @click="setTool('fitAll')">Fit</AButton>
            </ATooltip>
          </AButtonGroup>

          <ADivider type="vertical" />

          <!-- Selection Group -->
          <AButtonGroup size="small">
            <ATooltip title="Select mode">
              <AButton :type="currentTool === 'select' ? 'primary' : 'default'" @click="setTool('select')">Select</AButton>
            </ATooltip>
            <ATooltip title="Isolate selected">
              <AButton @click="setTool('isolate')">Isolate</AButton>
            </ATooltip>
            <ATooltip title="Show all objects">
              <AButton @click="setTool('showAll')">Show All</AButton>
            </ATooltip>
            <ATooltip title="X-Ray mode (X)">
              <AButton @click="setTool('xray')">X-Ray</AButton>
            </ATooltip>
          </AButtonGroup>

          <ADivider type="vertical" />

          <!-- Measurement Group -->
          <AButtonGroup size="small">
            <ATooltip title="Measure distance">
              <AButton :type="currentTool === 'measureDistance' ? 'primary' : 'default'" @click="setTool('measureDistance')">Distance</AButton>
            </ATooltip>
            <ATooltip title="Measure angle">
              <AButton :type="currentTool === 'measureAngle' ? 'primary' : 'default'" @click="setTool('measureAngle')">Angle</AButton>
            </ATooltip>
            <ATooltip title="Clear all measurements">
              <AButton @click="clearMeasurements">Clear</AButton>
            </ATooltip>
          </AButtonGroup>

          <ADivider type="vertical" />

          <!-- Section Group -->
          <AButtonGroup size="small">
            <ATooltip title="Add section plane">
              <AButton @click="setTool('section')">Section</AButton>
            </ATooltip>
            <ATooltip title="Flip all section planes">
              <AButton @click="flipAllSectionPlanes">Flip All</AButton>
            </ATooltip>
            <ATooltip title="Clear all sections">
              <AButton @click="clearSections">Clear</AButton>
            </ATooltip>
          </AButtonGroup>

          <ADivider type="vertical" />

          <!-- Annotation Group -->
          <AButtonGroup size="small">
            <ATooltip title="Add annotation (click on model)">
              <AButton :type="currentTool === 'annotate' ? 'primary' : 'default'" @click="setTool('annotate')">Annotate</AButton>
            </ATooltip>
            <ATooltip :title="annotationsVisible ? 'Hide annotations' : 'Show annotations'">
              <AButton @click="toggleAnnotationsVisible">{{ annotationsVisible ? 'Hide' : 'Show' }}</AButton>
            </ATooltip>
          </AButtonGroup>

          <ADivider type="vertical" />

          <!-- View Group -->
          <AButtonGroup size="small">
            <ATooltip title="Save BCF viewpoint">
              <AButton @click="saveViewpoint">Save View</AButton>
            </ATooltip>
            <ATooltip title="Toggle IFC tree panel">
              <AButton :type="showTreePanel ? 'primary' : 'default'" @click="toggleTreePanel">Tree</AButton>
            </ATooltip>
            <ATooltip title="Toggle properties panel">
              <AButton :type="showProperties ? 'primary' : 'default'" @click="showProperties = !showProperties">Props</AButton>
            </ATooltip>
            <ATooltip title="Section planes panel">
              <AButton :type="showSectionPanel ? 'primary' : 'default'" @click="showSectionPanel = !showSectionPanel; refreshSectionPlanesList()">Sections</AButton>
            </ATooltip>
            <ATooltip title="Measurements panel">
              <AButton :type="showMeasurementPanel ? 'primary' : 'default'" @click="showMeasurementPanel = !showMeasurementPanel; refreshMeasurementsList()">Measures</AButton>
            </ATooltip>
            <ATooltip title="Annotations panel">
              <AButton :type="showAnnotationPanel ? 'primary' : 'default'" @click="showAnnotationPanel = !showAnnotationPanel">Annotations</AButton>
            </ATooltip>
          </AButtonGroup>

          <ADivider type="vertical" />

          <!-- Models Group -->
          <AButtonGroup size="small">
            <ATooltip title="Load additional model">
              <AButton @click="openLoadModelModal">+ Model</AButton>
            </ATooltip>
            <ATooltip title="Loaded models list">
              <AButton :type="showModelListPanel ? 'primary' : 'default'" @click="showModelListPanel = !showModelListPanel">Models</AButton>
            </ATooltip>
          </AButtonGroup>
        </div>
      </div>

      <!-- ═══════════ MAIN CONTENT ═══════════ -->
      <div class="bim-main">
        <!-- IFC Tree Sidebar (left) -->
        <div v-show="showTreePanel" class="bim-tree-sidebar">
          <div class="bim-panel-head">
            <strong>IFC Structure</strong>
            <AButton type="text" size="small" @click="showTreePanel = false">X</AButton>
          </div>
          <div id="bim-tree-container" class="bim-tree-content"></div>
          <div class="bim-tree-actions">
            <ASpace size="small">
              <AButton size="small" @click="setTool('showAll')">Show All</AButton>
            </ASpace>
          </div>
        </div>

        <!-- 3D Viewer -->
        <div class="bim-viewer-container">
          <canvas id="xeokit-canvas" class="bim-canvas" />
          <canvas id="navcube-canvas" class="navcube-canvas" />
          <canvas id="section-overview-canvas" class="section-canvas" v-show="showSectionOverview" />

          <!-- Tool indicator -->
          <div v-if="currentTool !== 'select'" class="bim-tool-indicator">
            <ATag color="blue">{{ currentTool }}</ATag>
            <AButton type="link" size="small" @click="setTool('select')" style="font-size:11px;">ESC to cancel</AButton>
          </div>

          <!-- Loading -->
          <div v-if="loading" class="bim-loading">
            <ASpin size="large" />
            <div style="margin-top: 12px; font-size: 13px; color: #555">Loading model... {{ loadProgress }}%</div>
            <AProgress :percent="loadProgress" :show-info="false" style="width: 200px; margin-top: 8px" />
          </div>

          <!-- Properties Panel -->
          <div v-if="showProperties && selectedObject" class="bim-props">
            <div class="bim-panel-head">
              <strong>{{ selectedObject.name }}</strong>
              <AButton type="text" size="small" @click="showProperties = false">X</AButton>
            </div>
            <div class="bim-props-body">
              <div class="prop-r">
                <span class="prop-l">Entity ID</span>
                <span class="prop-v" style="font-family: monospace">{{ selectedObject.entityId }}</span>
              </div>
              <div class="prop-r">
                <span class="prop-l">IFC Type</span>
                <ATag color="blue" size="small">{{ selectedObject.type }}</ATag>
              </div>
              <div class="prop-r" style="gap:4px;margin-top:4px;">
                <AButton size="small" @click="treeIsolate(selectedObject.entityId)">Isolate</AButton>
                <AButton size="small" @click="treeHide(selectedObject.entityId)">Hide</AButton>
                <AButton size="small" @click="treeXRay(selectedObject.entityId)">X-Ray</AButton>
                <AButton size="small" @click="treeFlyTo(selectedObject.entityId)">Fly To</AButton>
              </div>
              <template v-if="selectedObject.properties">
                <template v-for="(propSet, setName) in selectedObject.properties" :key="setName">
                  <div style="font-size: 10px; font-weight: 600; color: #555; margin-top: 6px; border-top: 1px solid #f0f0f0; padding-top: 4px">{{ setName }}</div>
                  <div v-for="(val, key) in propSet" :key="key" class="prop-r">
                    <span class="prop-l">{{ key }}</span>
                    <span class="prop-v">{{ val }}</span>
                  </div>
                </template>
              </template>
            </div>
          </div>

          <!-- Section Planes Panel -->
          <div v-if="showSectionPanel" class="bim-right-panel" style="top: 12px; right: 170px">
            <div class="bim-panel-head">
              <strong>Section Planes</strong>
              <AButton type="text" size="small" @click="showSectionPanel = false">X</AButton>
            </div>
            <div class="bim-panel-body">
              <div v-if="sectionPlanesList.length === 0" class="bim-empty-msg">No section planes. Click "Section" to add one.</div>
              <div v-for="sp in sectionPlanesList" :key="sp.id" class="bim-list-item">
                <div style="flex: 1; min-width: 0">
                  <div style="font-size: 11px; font-weight: 500">{{ sp.id }}</div>
                  <div style="font-size: 10px; color: #999">Dir: {{ formatDir(sp.dir) }}</div>
                </div>
                <ASpace size="small">
                  <ATooltip title="Flip direction">
                    <AButton size="small" @click="flipSectionPlane(sp.id)">Flip</AButton>
                  </ATooltip>
                  <ATooltip title="Edit (show gizmo)">
                    <AButton size="small" @click="editSectionPlane(sp.id)">Edit</AButton>
                  </ATooltip>
                  <ATooltip :title="sp.active ? 'Deactivate' : 'Activate'">
                    <AButton size="small" :type="sp.active ? 'primary' : 'default'" @click="toggleSectionPlaneActive(sp.id)">{{ sp.active ? 'On' : 'Off' }}</AButton>
                  </ATooltip>
                  <ATooltip title="Delete plane">
                    <AButton size="small" danger @click="deleteSectionPlane(sp.id)">Del</AButton>
                  </ATooltip>
                </ASpace>
              </div>
              <div v-if="sectionPlanesList.length > 0" style="padding: 6px 8px; border-top: 1px solid #f0f0f0">
                <AButton size="small" block @click="flipAllSectionPlanes">Flip All Planes</AButton>
              </div>
            </div>
          </div>

          <!-- Measurement Panel -->
          <div v-if="showMeasurementPanel" class="bim-right-panel" style="top: 12px; right: 170px">
            <div class="bim-panel-head">
              <strong>Measurements</strong>
              <AButton type="text" size="small" @click="showMeasurementPanel = false">X</AButton>
            </div>
            <div class="bim-panel-body">
              <div v-if="distanceMeasurementsList.length === 0 && angleMeasurementsList.length === 0" class="bim-empty-msg">
                No measurements. Use Distance or Angle tools.
              </div>
              <template v-if="distanceMeasurementsList.length > 0">
                <div class="bim-panel-section-title">Distance</div>
                <div v-for="m in distanceMeasurementsList" :key="'d-' + m.id" class="bim-list-item">
                  <div style="flex: 1; font-size: 11px">{{ m.id }}: <strong>{{ m.length }} m</strong></div>
                  <AButton size="small" danger @click="deleteDistanceMeasurement(m.id)">Del</AButton>
                </div>
              </template>
              <template v-if="angleMeasurementsList.length > 0">
                <div class="bim-panel-section-title">Angle</div>
                <div v-for="m in angleMeasurementsList" :key="'a-' + m.id" class="bim-list-item">
                  <div style="flex: 1; font-size: 11px">{{ m.id }}: <strong>{{ m.angle }}°</strong></div>
                  <AButton size="small" danger @click="deleteAngleMeasurement(m.id)">Del</AButton>
                </div>
              </template>
              <div style="padding: 6px 8px; border-top: 1px solid #f0f0f0">
                <AButton size="small" block danger @click="clearMeasurements">Clear All</AButton>
              </div>
            </div>
          </div>

          <!-- Annotation Panel -->
          <div v-if="showAnnotationPanel" class="bim-right-panel" style="top: 12px; right: 170px">
            <div class="bim-panel-head">
              <strong>Annotations</strong>
              <AButton type="text" size="small" @click="showAnnotationPanel = false">X</AButton>
            </div>
            <div class="bim-panel-body">
              <div v-if="annotationsList.length === 0" class="bim-empty-msg">No annotations. Use the Annotate tool to add one.</div>
              <div v-for="ann in annotationsList" :key="ann.id" class="bim-list-item" style="flex-direction: column; align-items: flex-start">
                <div style="display: flex; justify-content: space-between; width: 100%; align-items: center">
                  <div style="font-size: 11px; font-weight: 500; cursor: pointer" @click="flyToAnnotation(ann)">{{ ann.title }}</div>
                  <ASpace size="small">
                    <ATag :color="priorityColors[ann.priority]" size="small">{{ ann.priority }}</ATag>
                    <ATag :color="statusColors[ann.status]" size="small">{{ ann.status }}</ATag>
                  </ASpace>
                </div>
                <div v-if="ann.description" style="font-size: 10px; color: #888; margin-top: 2px">{{ ann.description }}</div>
                <ASpace size="small" style="margin-top: 4px">
                  <AButton size="small" @click="flyToAnnotation(ann)">Fly To</AButton>
                  <AButton v-if="ann.status !== 'resolved'" size="small" type="primary" @click="resolveAnnotation(ann)">Resolve</AButton>
                  <AButton size="small" danger @click="deleteAnnotation(ann)">Delete</AButton>
                </ASpace>
              </div>
            </div>
          </div>

          <!-- Model List Panel -->
          <div v-if="showModelListPanel" class="bim-right-panel" style="top: 12px; right: 170px">
            <div class="bim-panel-head">
              <strong>Loaded Models</strong>
              <AButton type="text" size="small" @click="showModelListPanel = false">X</AButton>
            </div>
            <div class="bim-panel-body">
              <div v-if="loadedModels.length === 0" class="bim-empty-msg">No models loaded.</div>
              <div v-for="entry in loadedModels" :key="entry.id" class="bim-list-item">
                <div style="flex: 1; min-width: 0">
                  <div style="font-size: 11px; font-weight: 500">{{ entry.name }}</div>
                  <div style="font-size: 10px; color: #999">{{ entry.discipline || 'N/A' }} &middot; .{{ entry.format }}</div>
                </div>
                <ASpace size="small">
                  <AButton size="small" @click="toggleModelVisibility(entry)">{{ entry.visible ? 'Hide' : 'Show' }}</AButton>
                  <AButton size="small" danger @click="unloadModel(entry)">Unload</AButton>
                </ASpace>
              </div>
              <div style="padding: 6px 8px; border-top: 1px solid #f0f0f0">
                <AButton size="small" block type="primary" @click="openLoadModelModal">Load Model</AButton>
              </div>
            </div>
          </div>

          <!-- Model info badge -->
          <div v-if="modelData" class="bim-info">
            <strong>{{ modelData.name }}</strong>
            <span style="color: #999; font-size: 10px; margin-left: 6px">.{{ modelData.file_format }}</span>
            <ATag :color="modelData.status === 'ready' ? 'green' : 'orange'" size="small" style="margin-left: 6px">{{ modelData.status }}</ATag>
            <ATag v-if="loadedModels.length > 1" color="purple" size="small" style="margin-left: 4px">{{ loadedModels.length }} models</ATag>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════════ ANNOTATION DRAWER ═══════════ -->
    <ADrawer
      v-model:open="annotationDrawerVisible"
      title="New Annotation"
      placement="right"
      :width="360"
      @close="annotationDrawerVisible = false"
    >
      <AForm layout="vertical">
        <AFormItem label="Title" required>
          <AInput v-model:value="annotationForm.title" placeholder="Annotation title" :maxlength="255" />
        </AFormItem>
        <AFormItem label="Description">
          <ATextarea v-model:value="annotationForm.description" placeholder="Description (optional)" :rows="3" />
        </AFormItem>
        <AFormItem label="Priority">
          <ASelect v-model:value="annotationForm.priority" style="width: 100%">
            <ASelectOption value="low">Low</ASelectOption>
            <ASelectOption value="medium">Medium</ASelectOption>
            <ASelectOption value="high">High</ASelectOption>
            <ASelectOption value="critical">Critical</ASelectOption>
          </ASelect>
        </AFormItem>
        <AFormItem label="Position">
          <div style="font-size: 11px; color: #888; font-family: monospace">
            X: {{ annotationForm.world_pos_x.toFixed(3) }},
            Y: {{ annotationForm.world_pos_y.toFixed(3) }},
            Z: {{ annotationForm.world_pos_z.toFixed(3) }}
          </div>
        </AFormItem>
        <AFormItem v-if="annotationForm.entity_id" label="Entity">
          <ATag color="blue">{{ annotationForm.entity_id }}</ATag>
        </AFormItem>
        <AButton type="primary" block :loading="savingAnnotation" @click="saveAnnotation">Save Annotation</AButton>
      </AForm>
    </ADrawer>

    <!-- ═══════════ LOAD MODEL MODAL ═══════════ -->
    <AModal
      v-model:open="loadModelModalVisible"
      title="Load Additional Model"
      :footer="null"
      :width="500"
    >
      <div v-if="availableModels.length === 0" style="text-align: center; padding: 24px; color: #999">
        No additional models available for this project.
      </div>
      <AList
        v-else
        :dataSource="availableModels"
        size="small"
      >
        <template #renderItem="{ item }">
          <AListItem>
            <AListItemMeta
              :title="item.name"
              :description="`${item.discipline || 'N/A'} &middot; .${item.file_format || '?'} &middot; v${item.version}`"
            />
            <template #actions>
              <AButton size="small" type="primary" :loading="loadingAdditionalModel" @click="loadAdditionalModel(item)">Load</AButton>
            </template>
          </AListItem>
        </template>
      </AList>
    </AModal>
  </Page>
</template>

<style scoped>
.bim-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 120px);
}

.bim-toolbar {
  padding: 4px 8px;
  background: #fafafa;
  border-bottom: 1px solid #e8e8e8;
  flex-shrink: 0;
  overflow-x: auto;
}

.bim-toolbar-inner {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: nowrap;
  min-width: max-content;
}

.bim-main {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* IFC Tree Sidebar */
.bim-tree-sidebar {
  width: 280px;
  min-width: 280px;
  border-right: 1px solid #e8e8e8;
  background: #fff;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.bim-tree-content {
  flex: 1;
  overflow-y: auto;
  padding: 4px;
  font-size: 12px;
}

.bim-tree-actions {
  padding: 6px 8px;
  border-top: 1px solid #f0f0f0;
  background: #fafafa;
}

/* Viewer Container */
.bim-viewer-container {
  position: relative;
  flex: 1;
  overflow: hidden;
  background: linear-gradient(135deg, #e8edf2, #f5f5f5, #ffffff);
}

.bim-canvas {
  width: 100%;
  height: 100%;
  display: block;
}

.navcube-canvas {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 150px;
  height: 150px;
  z-index: 10;
}

.section-canvas {
  position: absolute;
  bottom: 12px;
  right: 12px;
  width: 200px;
  height: 200px;
  z-index: 10;
  border: 1px solid #ccc;
  border-radius: 6px;
  background: #fff;
}

.bim-tool-indicator {
  position: absolute;
  bottom: 12px;
  left: 12px;
  z-index: 15;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 4px 10px;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
}

.bim-loading {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.88);
  z-index: 20;
}

/* Panel Shared Styles */
.bim-panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid #f0f0f0;
  background: #fafafa;
  font-size: 12px;
  flex-shrink: 0;
}

/* Properties Panel */
.bim-props {
  position: absolute;
  top: 12px;
  right: 170px;
  width: 280px;
  max-height: calc(100% - 24px);
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  z-index: 15;
  overflow-y: auto;
}

.bim-props-body {
  padding: 8px 12px;
  font-size: 11px;
}

.prop-r {
  display: flex;
  justify-content: space-between;
  padding: 2px 0;
  border-bottom: 1px solid #f8f8f8;
}

.prop-l {
  color: #888;
  font-size: 10px;
}

.prop-v {
  color: #333;
  font-size: 10px;
  max-width: 160px;
  word-break: break-all;
}

/* Right-side panels (sections, measurements, annotations, models) */
.bim-right-panel {
  position: absolute;
  width: 300px;
  max-height: calc(100% - 24px);
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  z-index: 16;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.bim-panel-body {
  flex: 1;
  overflow-y: auto;
  max-height: 400px;
}

.bim-list-item {
  display: flex;
  align-items: center;
  padding: 6px 8px;
  border-bottom: 1px solid #f5f5f5;
  gap: 6px;
}

.bim-list-item:hover {
  background: #fafafa;
}

.bim-empty-msg {
  padding: 16px;
  text-align: center;
  color: #bbb;
  font-size: 11px;
}

.bim-panel-section-title {
  font-size: 10px;
  font-weight: 600;
  color: #555;
  padding: 6px 8px 2px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Model info badge */
.bim-info {
  position: absolute;
  top: 12px;
  left: 12px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 6px 12px;
  z-index: 15;
  font-size: 12px;
  display: flex;
  align-items: center;
}

/* Annotation marker styling (used by AnnotationsPlugin) */
:deep(.bim-annotation-marker) {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #1890ff;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  border: 2px solid #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.3);
  cursor: pointer;
}

:deep(.bim-annotation-label) {
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: 6px 10px;
  font-size: 11px;
  max-width: 200px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.12);
}

:deep(.bim-annotation-label b) {
  display: block;
  margin-bottom: 2px;
}

:deep(.bim-annotation-label p) {
  margin: 0;
  color: #888;
  font-size: 10px;
}

/* xeokit TreeViewPlugin styling */
:deep(#bim-tree-container ul) {
  list-style: none;
  padding-left: 14px;
  margin: 0;
}

:deep(#bim-tree-container li) {
  padding: 1px 0;
}

:deep(#bim-tree-container .xeokit-tree-node-title) {
  font-size: 11px;
  cursor: pointer;
  padding: 2px 4px;
  border-radius: 3px;
}

:deep(#bim-tree-container .xeokit-tree-node-title:hover) {
  background: #e6f7ff;
}

:deep(#bim-tree-container .xeokit-tree-node-title.highlighted) {
  background: #bae7ff;
}
</style>
