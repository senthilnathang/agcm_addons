<script setup>
/**
 * BIM 3D Viewer — Phase 4: Advanced Features
 *
 * Phase 1+2 Features (preserved):
 * - XKT model loading with multi-model federation
 * - IFC Tree Panel (spatial hierarchy browser)
 * - Section Planes Panel with interactive controls
 * - Measurement Panel (distance + angle listing)
 * - 3D Annotations with backend persistence
 * - Enhanced toolbar with grouped tools
 * - Keyboard shortcuts
 * - NavCube, BCF viewpoints, object selection
 *
 * Phase 3 Features (preserved):
 * - BCF Viewpoints Panel with save/load/share (full BCF 2.1 JSON)
 * - Annotation List Panel with filtering by status/priority
 * - Snapshot export (PNG download)
 * - Share viewpoint via URL
 * - Cross-entity linking (viewpoints linked to RFIs, Issues)
 * - Enhanced keyboard shortcuts (V, A, S, 1-5)
 *
 * Phase 4 Features (new):
 * - Storey plan views (2D floor plans from 3D model)
 * - First-person walkthrough with HUD controls
 * - IFC type color customization panel
 * - Object colorize by property / discipline presets
 * - Model explosion view with slider
 * - Enhanced snapshot with annotations overlay + watermark
 * - Performance optimization panel (SAO, edges, PBR, FPS counter)
 * - Additional keyboard shortcuts (P, E, C, G)
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
  StoreyViewsPlugin,
  math,
} from '@xeokit/xeokit-sdk';

import { Page } from '@vben/common-ui';
import { requestClient } from '#/api/request';

defineOptions({ name: 'AGCMBIMViewer' });

const route = useRoute();
const router = useRouter();
const BASE = '/agcm_bim';

// ═══════════════════════════════════════════════════════════
// STATE — Phase 1+2
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

// ═══════════════════════════════════════════════════════════
// STATE — Phase 3: Collaboration
// ═══════════════════════════════════════════════════════════

const showViewpointsPanel = ref(false);
const viewpointsList = ref([]);
const loadingViewpoints = ref(false);
const savingViewpoint = ref(false);
const viewpointNameInput = ref('');

// Annotation filtering
const annotationFilterStatus = ref('all');
const annotationFilterPriority = ref('all');

// Link entity modal
const linkEntityModalVisible = ref(false);
const linkEntityTarget = ref(null); // { type: 'viewpoint'|'annotation', id: ... }
const linkEntityForm = reactive({ entity_type: 'rfi', entity_id: null });

// Viewpoint from URL query param
const initialViewpointId = ref(route.query.viewpoint ? Number(route.query.viewpoint) : null);

// ═══════════════════════════════════════════════════════════
// STATE — Phase 4: Advanced Features
// ═══════════════════════════════════════════════════════════

// A. Storey Plan Views
const showStoreysPanel = ref(false);
const storeysList = ref([]);
const activeStoreyId = ref(null);
const inPlanViewMode = ref(false);

// B. First-Person Walkthrough
const walkSpeed = ref(1.5);
const constrainVertical = ref(false);

// C. IFC Type Color Customization
const showColorsPanel = ref(false);
const ifcTypeColors = reactive({
  IfcWall:                  { color: '#C8C8C8', visible: true },
  IfcSlab:                  { color: '#A0A0A0', visible: true },
  IfcColumn:                { color: '#B0B0B0', visible: true },
  IfcBeam:                  { color: '#B8B8B8', visible: true },
  IfcDoor:                  { color: '#8B6914', visible: true },
  IfcWindow:                { color: '#5656DF', visible: true },
  IfcStair:                 { color: '#D0D0D0', visible: true },
  IfcRoof:                  { color: '#CC6633', visible: true },
  IfcCurtainWall:           { color: '#6699CC', visible: true },
  IfcPipeSegment:           { color: '#33AA33', visible: true },
  IfcDuctSegment:           { color: '#339999', visible: true },
  IfcCableCarrierSegment:   { color: '#CC9933', visible: true },
  IfcFurnishingElement:     { color: '#996633', visible: true },
  IfcSpace:                 { color: '#EEEEEE', visible: false },
});
const colorPresetsApplied = ref('none');

// D. Model Explosion View
const showExplosionSlider = ref(false);
const explosionFactor = ref(0);

// E. Enhanced Snapshot
const snapshotIncludeWatermark = ref(true);

// F. Performance Optimization
const showPerformancePanel = ref(false);
const perfSaoEnabled = ref(true);
const perfEdgesEnabled = ref(true);
const perfPbrEnabled = ref(false);
const fpsCount = ref(0);
const objectCount = ref(0);
const perfPreset = ref('custom');

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
let storeyViewsPlugin = null;

// FPS tracking
let fpsFrameCount = 0;
let fpsLastTime = 0;
let fpsAnimationId = null;

// ═══════════════════════════════════════════════════════════
// COMPUTED — Phase 3
// ═══════════════════════════════════════════════════════════

const filteredAnnotations = computed(() => {
  let list = annotationsList.value;
  if (annotationFilterStatus.value !== 'all') {
    list = list.filter((a) => a.status === annotationFilterStatus.value);
  }
  if (annotationFilterPriority.value !== 'all') {
    list = list.filter((a) => a.priority === annotationFilterPriority.value);
  }
  return list;
});

// ═══════════════════════════════════════════════════════════
// COMPUTED — Phase 4
// ═══════════════════════════════════════════════════════════

const isFirstPersonMode = computed(() => currentTool.value === 'firstPerson');

const ifcTypeList = computed(() => {
  return Object.keys(ifcTypeColors).map((type) => ({
    type,
    color: ifcTypeColors[type].color,
    visible: ifcTypeColors[type].visible,
  }));
});

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
    authoringTool: 'BuildForge BIM Viewer v4.0',
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

  // Phase 4: StoreyViewsPlugin
  storeyViewsPlugin = new StoreyViewsPlugin(viewer, {
    fitStoreysContainingPickedObject: false,
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

  // Phase 4: Start FPS counter
  startFpsCounter();

  // Phase 4: Load saved color presets from localStorage
  loadColorPresetsFromStorage();

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
      src: `/api/v1${BASE}/models/${id}/xkt?token=${localStorage.getItem('accessToken') || ''}`,
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

      // Load saved viewpoints
      loadViewpoints();

      refreshMeasurementsList();
      refreshSectionPlanesList();

      // Phase 4: detect storeys
      refreshStoreysList();

      // Phase 4: update object count
      updateObjectCount();

      // Auto-restore viewpoint from URL query param
      if (initialViewpointId.value) {
        restoreViewpointById(initialViewpointId.value);
        initialViewpointId.value = null;
      }
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
  refreshStoreysList();
  updateObjectCount();
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
  // Close storeys panel if opening tree
  if (showTreePanel.value) {
    showStoreysPanel.value = false;
  }
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
// PHASE 3: BCF VIEWPOINTS PANEL
// ═══════════════════════════════════════════════════════════

async function loadViewpoints() {
  if (!modelId.value) return;
  loadingViewpoints.value = true;
  try {
    const result = await requestClient.get(`${BASE}/viewpoints`, {
      params: { model_id: modelId.value, page_size: 100 },
    });
    viewpointsList.value = result.items || result || [];
  } catch (e) {
    console.error('Failed to load viewpoints:', e);
  } finally {
    loadingViewpoints.value = false;
  }
}

async function saveCurrentViewpoint() {
  if (!bcfViewpoints || !modelId.value) return;
  savingViewpoint.value = true;
  try {
    // Get full BCF 2.1 JSON from plugin
    const bcfData = bcfViewpoints.getViewpoint({
      spacesVisible: false,
      openingsVisible: false,
      snapshot: false,
      defaultInvisible: true,
    });

    // Take screenshot
    let snapshotBase64 = null;
    try {
      snapshotBase64 = viewer.getSnapshot({ format: 'png', width: 300, height: 200 });
    } catch (e) {
      console.warn('Snapshot capture failed:', e);
    }

    const name = viewpointNameInput.value.trim() || `Viewpoint ${new Date().toLocaleString()}`;

    const payload = {
      model_id: modelId.value,
      name: name,
      bcf_data: JSON.stringify(bcfData),
      camera_position: JSON.stringify(bcfData.perspective_camera || bcfData.orthographic_camera || {}),
      camera_target: JSON.stringify({
        x: viewer.camera.look[0],
        y: viewer.camera.look[1],
        z: viewer.camera.look[2],
      }),
      snapshot_base64: snapshotBase64 || null,
      annotations: JSON.stringify(bcfData),
    };

    await requestClient.post(`${BASE}/viewpoints`, payload);
    viewpointNameInput.value = '';
    await loadViewpoints();
  } catch (e) {
    console.error('Save viewpoint failed:', e);
  } finally {
    savingViewpoint.value = false;
  }
}

async function restoreViewpoint(vp) {
  if (!bcfViewpoints) return;
  try {
    // Parse full BCF data if available
    const bcfData = vp.bcf_data ? JSON.parse(vp.bcf_data) : null;
    if (bcfData) {
      bcfViewpoints.setViewpoint(bcfData, { immediate: false, duration: 0.5 });
    } else if (vp.camera_position) {
      // Fallback to simple camera restore
      const cam = JSON.parse(vp.camera_position);
      const target = vp.camera_target ? JSON.parse(vp.camera_target) : null;
      if (cam && target) {
        viewer.cameraFlight.flyTo({
          eye: [cam.eye?.x ?? cam.x ?? 0, cam.eye?.y ?? cam.y ?? 0, cam.eye?.z ?? cam.z ?? 0],
          look: [target.x || 0, target.y || 0, target.z || 0],
          duration: 0.5,
        });
      }
    }
  } catch (e) {
    console.error('Failed to restore viewpoint:', e);
  }
}

async function restoreViewpointById(vpId) {
  try {
    const vp = await requestClient.get(`${BASE}/viewpoints/${vpId}`);
    if (vp) {
      restoreViewpoint(vp);
    }
  } catch (e) {
    console.error('Failed to load viewpoint by ID:', e);
  }
}

async function deleteViewpoint(vp) {
  try {
    await requestClient.delete(`${BASE}/viewpoints/${vp.id}`);
    await loadViewpoints();
  } catch (e) {
    console.error('Failed to delete viewpoint:', e);
  }
}

function copyViewpointLink(vp) {
  const url = `${window.location.origin}${window.location.pathname}?id=${modelId.value}&viewpoint=${vp.id}`;
  navigator.clipboard.writeText(url).then(() => {
    // Brief feedback — could use message API but keeping it simple
    console.log('Viewpoint link copied to clipboard');
  }).catch(() => {
    // Fallback: select-and-copy via temp textarea
    const ta = document.createElement('textarea');
    ta.value = url;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
  });
}

// ═══════════════════════════════════════════════════════════
// PHASE 3: LINK ENTITY
// ═══════════════════════════════════════════════════════════

function openLinkEntityModal(targetType, targetId) {
  linkEntityTarget.value = { type: targetType, id: targetId };
  linkEntityForm.entity_type = 'rfi';
  linkEntityForm.entity_id = null;
  linkEntityModalVisible.value = true;
}

async function submitLinkEntity() {
  if (!linkEntityTarget.value || !linkEntityForm.entity_id) return;
  const target = linkEntityTarget.value;
  try {
    if (target.type === 'viewpoint') {
      await requestClient.post(`${BASE}/viewpoints/${target.id}/link`, {
        entity_type: linkEntityForm.entity_type,
        entity_id: linkEntityForm.entity_id,
      });
      await loadViewpoints();
    } else if (target.type === 'annotation') {
      await requestClient.put(`${BASE}/annotations/${target.id}`, {
        linked_entity_type: linkEntityForm.entity_type,
        linked_entity_id: linkEntityForm.entity_id,
      });
      await loadAnnotations();
    }
    linkEntityModalVisible.value = false;
  } catch (e) {
    console.error('Failed to link entity:', e);
  }
}

// ═══════════════════════════════════════════════════════════
// PHASE 3: SNAPSHOT EXPORT (enhanced in Phase 4)
// ═══════════════════════════════════════════════════════════

function takeScreenshot() {
  if (!viewer) return;
  if (snapshotIncludeWatermark.value) {
    const modelName = modelData.value?.name || 'BIM Model';
    const dateStr = new Date().toLocaleString();
    snapshotWithWatermark(`${modelName} — ${dateStr}`);
  } else {
    takeSimpleScreenshot();
  }
}

function takeSimpleScreenshot() {
  try {
    const dataUrl = viewer.getSnapshot({ format: 'png', width: 1920, height: 1080 });
    const link = document.createElement('a');
    link.href = dataUrl;
    const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
    link.download = `bim-screenshot-${ts}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  } catch (e) {
    console.error('Screenshot failed:', e);
  }
}

function snapshotWithWatermark(text) {
  try {
    const snapshotData = viewer.getSnapshot({ format: 'png', width: 1920, height: 1080 });
    const canvas = document.createElement('canvas');
    canvas.width = 1920;
    canvas.height = 1080;
    const ctx = canvas.getContext('2d');
    const img = new Image();
    img.onload = () => {
      ctx.drawImage(img, 0, 0);
      // Watermark background
      ctx.fillStyle = 'rgba(255,255,255,0.7)';
      ctx.fillRect(0, 1050, 500, 30);
      // Watermark text
      ctx.font = '14px Arial';
      ctx.fillStyle = '#333';
      ctx.fillText(text, 10, 1068);
      // Section plane indicator
      if (sectionPlanesList.value.length > 0) {
        ctx.fillStyle = 'rgba(255, 100, 100, 0.6)';
        ctx.fillText(`[${sectionPlanesList.value.length} section plane(s) active]`, 10, 1046);
      }
      // Trigger download
      const link = document.createElement('a');
      const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
      link.download = `bim-snapshot-${ts}.png`;
      link.href = canvas.toDataURL('image/png');
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    };
    img.src = snapshotData;
  } catch (e) {
    console.error('Snapshot with watermark failed:', e);
    // Fallback to simple screenshot
    takeSimpleScreenshot();
  }
}

// ═══════════════════════════════════════════════════════════
// PHASE 4A: STOREY PLAN VIEWS
// ═══════════════════════════════════════════════════════════

function refreshStoreysList() {
  if (!viewer || !viewer.metaScene) return;
  const storeys = [];
  const metaObjects = viewer.metaScene.metaObjects;
  for (const id in metaObjects) {
    const mo = metaObjects[id];
    if (mo.type === 'IfcBuildingStorey') {
      storeys.push({
        id: mo.id,
        name: mo.name || mo.id,
        objectIds: viewer.metaScene.getObjectIDsInSubtree(mo.id),
      });
    }
  }
  // Sort storeys by name (typically level order)
  storeys.sort((a, b) => a.name.localeCompare(b.name, undefined, { numeric: true }));
  storeysList.value = storeys;
}

function toggleStoreysPanel() {
  showStoreysPanel.value = !showStoreysPanel.value;
  // Close tree panel if opening storeys
  if (showStoreysPanel.value) {
    showTreePanel.value = false;
  }
  nextTick(() => viewer?.scene?.canvas?.resizeCanvas?.());
}

function gotoStorey(storey) {
  if (!viewer) return;
  activeStoreyId.value = storey.id;
  inPlanViewMode.value = true;

  // Show all objects first, then isolate storey objects
  viewer.scene.setObjectsVisible(viewer.scene.objectIds, false);
  viewer.scene.setObjectsVisible(storey.objectIds, true);

  // Switch to plan view (top-down) camera
  viewer.cameraControl.navMode = 'planView';
  currentTool.value = 'planView';

  // Fly to the storey AABB from above
  const aabb = viewer.scene.getAABB(storey.objectIds);
  if (aabb) {
    const center = math.getAABB3Center(aabb);
    const height = aabb[4] + 20; // Above the storey
    viewer.cameraFlight.flyTo({
      eye: [center[0], height, center[2]],
      look: [center[0], center[1], center[2]],
      up: [0, 0, -1],
      duration: 0.8,
    });
  }
}

function exitPlanView() {
  if (!viewer) return;
  inPlanViewMode.value = false;
  activeStoreyId.value = null;

  // Restore all visibility
  viewer.scene.setObjectsVisible(viewer.scene.objectIds, true);
  // Restore excluded types
  const excludeTypes = ['IfcSpace', 'IfcOpeningElement'];
  excludeTypes.forEach((type) => {
    const ids = getObjectIdsByType(type);
    if (ids.length) {
      viewer.scene.setObjectsVisible(ids, false);
    }
  });

  // Switch back to orbit mode
  viewer.cameraControl.navMode = 'orbit';
  currentTool.value = 'select';

  // Fit the whole model
  viewer.cameraFlight.flyTo({ aabb: viewer.scene.aabb, duration: 0.8 });
}

function togglePlanView() {
  if (inPlanViewMode.value) {
    exitPlanView();
  } else {
    // If storeys exist, go to first storey
    if (storeysList.value.length > 0) {
      gotoStorey(storeysList.value[0]);
    } else {
      // Just switch to plan view camera mode
      viewer.cameraControl.navMode = 'planView';
      currentTool.value = 'planView';
      inPlanViewMode.value = true;
    }
  }
}

// ═══════════════════════════════════════════════════════════
// PHASE 4B: FIRST-PERSON WALKTHROUGH ENHANCEMENT
// ═══════════════════════════════════════════════════════════

function onWalkSpeedChange(val) {
  walkSpeed.value = val;
  if (viewer && viewer.cameraControl) {
    viewer.cameraControl.walkSpeed = val;
  }
}

function onConstrainVerticalChange(val) {
  constrainVertical.value = val;
  if (viewer && viewer.cameraControl) {
    viewer.cameraControl.constrainVertical = val;
  }
}

function exitFirstPerson() {
  viewer.cameraControl.navMode = 'orbit';
  viewer.cameraControl.constrainVertical = false;
  currentTool.value = 'select';
}

// ═══════════════════════════════════════════════════════════
// PHASE 4C: IFC TYPE COLOR CUSTOMIZATION
// ═══════════════════════════════════════════════════════════

function getObjectIdsByType(ifcType) {
  if (!viewer || !viewer.metaScene) return [];
  const ids = [];
  const metaObjects = viewer.metaScene.metaObjects;
  for (const id in metaObjects) {
    if (metaObjects[id].type === ifcType) {
      ids.push(id);
    }
  }
  return ids;
}

function applyTypeColor(ifcType) {
  if (!viewer) return;
  const entry = ifcTypeColors[ifcType];
  if (!entry) return;
  const ids = getObjectIdsByType(ifcType);
  if (ids.length === 0) return;

  // Parse hex color to [r, g, b] 0-1 range
  const hex = entry.color;
  const r = parseInt(hex.slice(1, 3), 16) / 255;
  const g = parseInt(hex.slice(3, 5), 16) / 255;
  const b = parseInt(hex.slice(5, 7), 16) / 255;

  viewer.scene.setObjectsColorized(ids, [r, g, b]);
}

function onTypeColorChange(ifcType, hexColor) {
  ifcTypeColors[ifcType].color = hexColor;
  applyTypeColor(ifcType);
  saveColorPresetsToStorage();
}

function toggleTypeVisibility(ifcType) {
  if (!viewer) return;
  const entry = ifcTypeColors[ifcType];
  entry.visible = !entry.visible;
  const ids = getObjectIdsByType(ifcType);
  if (ids.length) {
    viewer.scene.setObjectsVisible(ids, entry.visible);
  }
  saveColorPresetsToStorage();
}

function resetAllColors() {
  if (!viewer) return;
  // Clear colorization on all objects
  viewer.scene.setObjectsColorized(viewer.scene.objectIds, null);
  colorPresetsApplied.value = 'none';

  // Reset to default colors
  const defaults = {
    IfcWall: '#C8C8C8', IfcSlab: '#A0A0A0', IfcColumn: '#B0B0B0',
    IfcBeam: '#B8B8B8', IfcDoor: '#8B6914', IfcWindow: '#5656DF',
    IfcStair: '#D0D0D0', IfcRoof: '#CC6633', IfcCurtainWall: '#6699CC',
    IfcPipeSegment: '#33AA33', IfcDuctSegment: '#339999',
    IfcCableCarrierSegment: '#CC9933', IfcFurnishingElement: '#996633',
    IfcSpace: '#EEEEEE',
  };
  for (const type in defaults) {
    if (ifcTypeColors[type]) {
      ifcTypeColors[type].color = defaults[type];
    }
  }
  saveColorPresetsToStorage();
}

function applyDisciplinePreset() {
  if (!viewer) return;
  colorPresetsApplied.value = 'discipline';

  // Architecture = blue
  const archTypes = ['IfcWall', 'IfcSlab', 'IfcDoor', 'IfcWindow', 'IfcStair', 'IfcRoof', 'IfcCurtainWall'];
  archTypes.forEach((type) => {
    if (ifcTypeColors[type]) ifcTypeColors[type].color = '#4488CC';
    const ids = getObjectIdsByType(type);
    if (ids.length) viewer.scene.setObjectsColorized(ids, [0.267, 0.533, 0.8]);
  });

  // Structural = red
  const structTypes = ['IfcColumn', 'IfcBeam'];
  structTypes.forEach((type) => {
    if (ifcTypeColors[type]) ifcTypeColors[type].color = '#CC4444';
    const ids = getObjectIdsByType(type);
    if (ids.length) viewer.scene.setObjectsColorized(ids, [0.8, 0.267, 0.267]);
  });

  // MEP = green
  const mepTypes = ['IfcPipeSegment', 'IfcDuctSegment', 'IfcCableCarrierSegment'];
  mepTypes.forEach((type) => {
    if (ifcTypeColors[type]) ifcTypeColors[type].color = '#44AA44';
    const ids = getObjectIdsByType(type);
    if (ids.length) viewer.scene.setObjectsColorized(ids, [0.267, 0.667, 0.267]);
  });

  // Furnishing = brown
  const furnTypes = ['IfcFurnishingElement'];
  furnTypes.forEach((type) => {
    if (ifcTypeColors[type]) ifcTypeColors[type].color = '#AA7744';
    const ids = getObjectIdsByType(type);
    if (ids.length) viewer.scene.setObjectsColorized(ids, [0.667, 0.467, 0.267]);
  });

  saveColorPresetsToStorage();
}

function applyAllTypeColors() {
  Object.keys(ifcTypeColors).forEach((type) => applyTypeColor(type));
}

function saveColorPresetsToStorage() {
  try {
    const data = {};
    for (const type in ifcTypeColors) {
      data[type] = { color: ifcTypeColors[type].color, visible: ifcTypeColors[type].visible };
    }
    localStorage.setItem('bim-viewer-color-presets', JSON.stringify(data));
  } catch (e) {
    // localStorage may be unavailable
  }
}

function loadColorPresetsFromStorage() {
  try {
    const stored = localStorage.getItem('bim-viewer-color-presets');
    if (stored) {
      const data = JSON.parse(stored);
      for (const type in data) {
        if (ifcTypeColors[type]) {
          ifcTypeColors[type].color = data[type].color || ifcTypeColors[type].color;
          ifcTypeColors[type].visible = data[type].visible !== undefined ? data[type].visible : true;
        }
      }
    }
  } catch (e) {
    // Ignore parse errors
  }
}

// ═══════════════════════════════════════════════════════════
// PHASE 4D: MODEL EXPLOSION VIEW
// ═══════════════════════════════════════════════════════════

function explodeModel(factor) {
  if (!viewer) return;
  const sceneCenter = viewer.scene.center;
  const objectIds = viewer.scene.objectIds;
  for (let i = 0, len = objectIds.length; i < len; i++) {
    const id = objectIds[i];
    const entity = viewer.scene.objects[id];
    if (!entity) continue;
    if (factor === 0) {
      entity.offset = [0, 0, 0];
    } else {
      const objectCenter = math.getAABB3Center(entity.aabb);
      const direction = math.subVec3(objectCenter, sceneCenter, []);
      const dist = math.lenVec3(direction);
      if (dist > 0.001) {
        math.normalizeVec3(direction);
        entity.offset = math.mulVec3Scalar(direction, factor, []);
      }
    }
  }
}

function onExplosionFactorChange(val) {
  explosionFactor.value = val;
  explodeModel(val);
}

function resetExplosion() {
  explosionFactor.value = 0;
  explodeModel(0);
}

function toggleExplosionSlider() {
  showExplosionSlider.value = !showExplosionSlider.value;
  if (!showExplosionSlider.value && explosionFactor.value !== 0) {
    resetExplosion();
  }
}

// ═══════════════════════════════════════════════════════════
// PHASE 4F: PERFORMANCE OPTIMIZATION
// ═══════════════════════════════════════════════════════════

function updateObjectCount() {
  if (viewer) {
    objectCount.value = Object.keys(viewer.scene.objects).length;
  }
}

function startFpsCounter() {
  fpsLastTime = performance.now();
  fpsFrameCount = 0;

  function countFrame() {
    fpsFrameCount++;
    const now = performance.now();
    if (now - fpsLastTime >= 1000) {
      fpsCount.value = fpsFrameCount;
      fpsFrameCount = 0;
      fpsLastTime = now;
    }
    fpsAnimationId = requestAnimationFrame(countFrame);
  }
  fpsAnimationId = requestAnimationFrame(countFrame);
}

function stopFpsCounter() {
  if (fpsAnimationId) {
    cancelAnimationFrame(fpsAnimationId);
    fpsAnimationId = null;
  }
}

function toggleSao(enabled) {
  perfSaoEnabled.value = enabled;
  if (viewer) {
    viewer.scene.sao.enabled = enabled;
  }
  perfPreset.value = 'custom';
}

function toggleEdges(enabled) {
  perfEdgesEnabled.value = enabled;
  if (viewer) {
    viewer.scene.edgeMaterial.edges = enabled;
  }
  perfPreset.value = 'custom';
}

function togglePbr(enabled) {
  perfPbrEnabled.value = enabled;
  if (viewer) {
    viewer.scene.pbrEnabled = enabled;
  }
  perfPreset.value = 'custom';
}

function applyPerfPreset(preset) {
  perfPreset.value = preset;
  switch (preset) {
    case 'high':
      toggleSao(true);
      toggleEdges(true);
      togglePbr(false);
      perfPreset.value = 'high';
      break;
    case 'performance':
      toggleSao(false);
      toggleEdges(false);
      togglePbr(false);
      perfPreset.value = 'performance';
      break;
    case 'wireframe':
      toggleSao(false);
      toggleEdges(true);
      togglePbr(false);
      if (viewer) {
        viewer.scene.setObjectsXRayed(viewer.scene.objectIds, true);
      }
      perfPreset.value = 'wireframe';
      break;
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
      viewer.cameraControl.walkSpeed = walkSpeed.value;
      viewer.cameraControl.constrainVertical = constrainVertical.value;
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
// KEYBOARD SHORTCUTS — Phase 2 + Phase 3 + Phase 4
// ═══════════════════════════════════════════════════════════

function handleKeyDown(e) {
  // Don't intercept when typing in input fields
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.isContentEditable) {
    return;
  }

  switch (e.key) {
    case 'Escape':
      if (isFirstPersonMode.value) {
        exitFirstPerson();
      } else if (inPlanViewMode.value) {
        exitPlanView();
      } else {
        setTool('select');
        annotationDrawerVisible.value = false;
      }
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
    // Phase 3 shortcuts
    case 'v':
    case 'V':
      if (!e.ctrlKey && !e.metaKey) {
        e.preventDefault();
        showViewpointsPanel.value = !showViewpointsPanel.value;
      }
      break;
    case 'a':
    case 'A':
      if (!e.ctrlKey && !e.metaKey) {
        e.preventDefault();
        showAnnotationPanel.value = !showAnnotationPanel.value;
      }
      break;
    case 's':
    case 'S':
      if (!e.ctrlKey && !e.metaKey) {
        e.preventDefault();
        takeScreenshot();
      }
      break;
    case '1':
    case '2':
    case '3':
    case '4':
    case '5': {
      if (!e.ctrlKey && !e.metaKey) {
        e.preventDefault();
        const idx = parseInt(e.key) - 1;
        if (viewpointsList.value[idx]) {
          restoreViewpoint(viewpointsList.value[idx]);
        }
      }
      break;
    }
    // Phase 4 shortcuts
    case 'p':
    case 'P':
      if (!e.ctrlKey && !e.metaKey) {
        e.preventDefault();
        togglePlanView();
      }
      break;
    case 'e':
    case 'E':
      if (!e.ctrlKey && !e.metaKey) {
        e.preventDefault();
        toggleExplosionSlider();
      }
      break;
    case 'c':
    case 'C':
      if (!e.ctrlKey && !e.metaKey) {
        e.preventDefault();
        showColorsPanel.value = !showColorsPanel.value;
      }
      break;
    case 'g':
    case 'G':
      if (!e.ctrlKey && !e.metaKey) {
        e.preventDefault();
        showPerformancePanel.value = !showPerformancePanel.value;
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

const priorityColors = { low: 'default', medium: 'blue', high: 'orange', critical: 'red' };
const statusColors = { open: 'blue', in_progress: 'orange', resolved: 'green' };
const entityTypeLabels = { rfi: 'RFI', issue: 'Issue', clash: 'Clash', submittal: 'Submittal' };

function formatDir(dir) {
  return `[${dir.map((v) => v.toFixed(2)).join(', ')}]`;
}

function formatDate(dt) {
  if (!dt) return '';
  const d = new Date(dt);
  return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function formatIfcTypeName(type) {
  // IfcWall -> Wall, IfcPipeSegment -> Pipe Segment
  return type.replace(/^Ifc/, '').replace(/([A-Z])/g, ' $1').trim();
}

// ═══════════════════════════════════════════════════════════
// LIFECYCLE
// ═══════════════════════════════════════════════════════════

onMounted(() => initViewer());

onBeforeUnmount(() => {
  document.removeEventListener('keydown', handleKeyDown);
  stopFpsCounter();
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
            <ATooltip title="Plan view (top down) [P]">
              <AButton :type="currentTool === 'planView' ? 'primary' : 'default'" @click="togglePlanView">Plan</AButton>
            </ATooltip>
            <ATooltip title="Storey plan views">
              <AButton :type="showStoreysPanel ? 'primary' : 'default'" @click="toggleStoreysPanel">Storeys</AButton>
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

          <!-- Collaboration Group (Phase 3) -->
          <AButtonGroup size="small">
            <ATooltip title="Viewpoints panel (V)">
              <AButton :type="showViewpointsPanel ? 'primary' : 'default'" @click="showViewpointsPanel = !showViewpointsPanel">Viewpoints</AButton>
            </ATooltip>
            <ATooltip title="Annotations panel (A)">
              <AButton :type="showAnnotationPanel ? 'primary' : 'default'" @click="showAnnotationPanel = !showAnnotationPanel">Annotations</AButton>
            </ATooltip>
            <ATooltip title="Export screenshot (S)">
              <AButton @click="takeScreenshot">Screenshot</AButton>
            </ATooltip>
          </AButtonGroup>

          <ADivider type="vertical" />

          <!-- Visualization Group (Phase 4) -->
          <AButtonGroup size="small">
            <ATooltip title="Color by IFC type (C)">
              <AButton :type="showColorsPanel ? 'primary' : 'default'" @click="showColorsPanel = !showColorsPanel">Colors</AButton>
            </ATooltip>
            <ATooltip title="Explode model (E)">
              <AButton :type="showExplosionSlider ? 'primary' : 'default'" @click="toggleExplosionSlider">Explode</AButton>
            </ATooltip>
            <ATooltip title="Performance settings (G)">
              <AButton :type="showPerformancePanel ? 'primary' : 'default'" @click="showPerformancePanel = !showPerformancePanel">Perf</AButton>
            </ATooltip>
          </AButtonGroup>

          <ADivider type="vertical" />

          <!-- View Group -->
          <AButtonGroup size="small">
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

        <!-- Phase 4A: Storeys Sidebar (left, replaces tree) -->
        <div v-show="showStoreysPanel" class="bim-tree-sidebar">
          <div class="bim-panel-head">
            <strong>Building Storeys</strong>
            <AButton type="text" size="small" @click="showStoreysPanel = false">X</AButton>
          </div>
          <div class="bim-storeys-content">
            <div v-if="storeysList.length === 0" class="bim-empty-msg">No storeys detected in model.</div>
            <div
              v-for="storey in storeysList"
              :key="storey.id"
              class="bim-storey-item"
              :class="{ 'bim-storey-active': activeStoreyId === storey.id }"
              @click="gotoStorey(storey)"
            >
              <div class="bim-storey-icon">&#9632;</div>
              <div class="bim-storey-info">
                <div class="bim-storey-name">{{ storey.name }}</div>
                <div class="bim-storey-count">{{ storey.objectIds.length }} objects</div>
              </div>
              <ATag v-if="activeStoreyId === storey.id" color="blue" size="small">Active</ATag>
            </div>
          </div>
          <div class="bim-tree-actions">
            <ASpace size="small">
              <AButton v-if="inPlanViewMode" size="small" type="primary" @click="exitPlanView">Back to 3D</AButton>
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
          <div v-if="currentTool !== 'select' && !isFirstPersonMode" class="bim-tool-indicator">
            <ATag color="blue">{{ currentTool }}</ATag>
            <AButton type="link" size="small" @click="setTool('select')" style="font-size:11px;">ESC to cancel</AButton>
          </div>

          <!-- Phase 4A: Plan View indicator -->
          <div v-if="inPlanViewMode" class="bim-plan-view-indicator">
            <ATag color="green">Plan View</ATag>
            <span v-if="activeStoreyId" style="font-size: 11px; margin-left: 4px">{{ storeysList.find(s => s.id === activeStoreyId)?.name || '' }}</span>
            <AButton type="link" size="small" @click="exitPlanView" style="font-size:11px; margin-left: 6px;">Back to 3D</AButton>
          </div>

          <!-- Phase 4B: First-Person Walkthrough HUD -->
          <div v-if="isFirstPersonMode" class="bim-walk-hud">
            <div class="bim-walk-hud-title">First Person Mode</div>
            <div class="bim-walk-hud-controls">
              <span>WASD: Move</span>
              <span style="margin-left: 8px">Mouse: Look</span>
            </div>
            <div class="bim-walk-hud-speed">
              <span>Speed:</span>
              <input
                type="range"
                min="0.1"
                max="5"
                step="0.1"
                :value="walkSpeed"
                class="bim-walk-speed-slider"
                @input="onWalkSpeedChange(parseFloat($event.target.value))"
              />
              <span class="bim-walk-speed-value">{{ walkSpeed.toFixed(1) }}</span>
            </div>
            <div class="bim-walk-hud-option">
              <label class="bim-walk-checkbox-label">
                <input type="checkbox" :checked="constrainVertical" @change="onConstrainVerticalChange($event.target.checked)" />
                <span>Constrain to floor</span>
              </label>
            </div>
            <div class="bim-walk-hud-exit">Press ESC to exit</div>
          </div>

          <!-- Phase 4D: Explosion Slider -->
          <div v-if="showExplosionSlider" class="bim-explosion-panel">
            <div class="bim-panel-head">
              <strong>Explosion</strong>
              <AButton type="text" size="small" @click="toggleExplosionSlider">X</AButton>
            </div>
            <div style="padding: 10px 12px;">
              <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 11px; min-width: 50px;">Factor:</span>
                <input
                  type="range"
                  min="0"
                  max="100"
                  step="1"
                  :value="explosionFactor"
                  style="flex: 1;"
                  @input="onExplosionFactorChange(parseFloat($event.target.value))"
                />
                <span style="font-size: 11px; min-width: 30px; text-align: right;">{{ explosionFactor.toFixed(0) }}</span>
              </div>
              <AButton size="small" block style="margin-top: 8px;" @click="resetExplosion">Reset</AButton>
            </div>
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
                  <div style="flex: 1; font-size: 11px">{{ m.id }}: <strong>{{ m.angle }}deg</strong></div>
                  <AButton size="small" danger @click="deleteAngleMeasurement(m.id)">Del</AButton>
                </div>
              </template>
              <div style="padding: 6px 8px; border-top: 1px solid #f0f0f0">
                <AButton size="small" block danger @click="clearMeasurements">Clear All</AButton>
              </div>
            </div>
          </div>

          <!-- ═══════════ Phase 3: BCF Viewpoints Panel ═══════════ -->
          <div v-if="showViewpointsPanel" class="bim-right-panel bim-viewpoints-panel" style="top: 12px; right: 170px">
            <div class="bim-panel-head">
              <strong>Viewpoints</strong>
              <AButton type="text" size="small" @click="showViewpointsPanel = false">X</AButton>
            </div>
            <div class="bim-panel-body">
              <!-- Save current view -->
              <div class="bim-vp-save-bar">
                <AInput
                  v-model:value="viewpointNameInput"
                  size="small"
                  placeholder="Viewpoint name (optional)"
                  style="flex: 1"
                  @pressEnter="saveCurrentViewpoint"
                />
                <AButton size="small" type="primary" :loading="savingViewpoint" @click="saveCurrentViewpoint">Save View</AButton>
              </div>

              <div v-if="loadingViewpoints" style="text-align: center; padding: 16px"><ASpin size="small" /></div>
              <div v-else-if="viewpointsList.length === 0" class="bim-empty-msg">No saved viewpoints. Click "Save View" to create one.</div>

              <div v-for="(vp, idx) in viewpointsList" :key="vp.id" class="bim-vp-item" @click="restoreViewpoint(vp)">
                <div class="bim-vp-item-thumb">
                  <img v-if="vp.snapshot_base64" :src="vp.snapshot_base64" class="bim-vp-thumb-img" />
                  <div v-else class="bim-vp-thumb-placeholder">{{ idx + 1 }}</div>
                </div>
                <div class="bim-vp-item-info">
                  <div class="bim-vp-item-name">{{ vp.name }}</div>
                  <div class="bim-vp-item-date">{{ formatDate(vp.created_at) }}</div>
                  <div v-if="vp.entity_type" class="bim-vp-item-entity">
                    <ATag :color="vp.entity_type === 'rfi' ? 'blue' : vp.entity_type === 'issue' ? 'orange' : 'default'" size="small">
                      {{ entityTypeLabels[vp.entity_type] || vp.entity_type }} #{{ vp.entity_id }}
                    </ATag>
                  </div>
                  <div v-if="vp.tags" style="margin-top: 2px">
                    <ATag v-for="tag in vp.tags.split(',')" :key="tag" size="small" style="margin-right: 2px">{{ tag.trim() }}</ATag>
                  </div>
                </div>
                <div class="bim-vp-item-actions" @click.stop>
                  <ATooltip title="Copy share link">
                    <AButton size="small" @click="copyViewpointLink(vp)">Link</AButton>
                  </ATooltip>
                  <ATooltip title="Link to entity">
                    <AButton size="small" @click="openLinkEntityModal('viewpoint', vp.id)">Link</AButton>
                  </ATooltip>
                  <AButton size="small" danger @click="deleteViewpoint(vp)">Del</AButton>
                </div>
              </div>

              <div v-if="viewpointsList.length > 0" class="bim-vp-hint">
                Press 1-5 to quick-load viewpoints
              </div>
            </div>
          </div>

          <!-- ═══════════ Phase 3: Enhanced Annotation Panel ═══════════ -->
          <div v-if="showAnnotationPanel" class="bim-right-panel" style="top: 12px; right: 170px">
            <div class="bim-panel-head">
              <strong>Annotations</strong>
              <AButton type="text" size="small" @click="showAnnotationPanel = false">X</AButton>
            </div>
            <div class="bim-ann-filters">
              <ASelect v-model:value="annotationFilterStatus" size="small" style="width: 100px">
                <ASelectOption value="all">All Status</ASelectOption>
                <ASelectOption value="open">Open</ASelectOption>
                <ASelectOption value="in_progress">In Progress</ASelectOption>
                <ASelectOption value="resolved">Resolved</ASelectOption>
              </ASelect>
              <ASelect v-model:value="annotationFilterPriority" size="small" style="width: 100px">
                <ASelectOption value="all">All Priority</ASelectOption>
                <ASelectOption value="low">Low</ASelectOption>
                <ASelectOption value="medium">Medium</ASelectOption>
                <ASelectOption value="high">High</ASelectOption>
                <ASelectOption value="critical">Critical</ASelectOption>
              </ASelect>
            </div>
            <div class="bim-panel-body">
              <div v-if="filteredAnnotations.length === 0" class="bim-empty-msg">No annotations match filters.</div>
              <div v-for="ann in filteredAnnotations" :key="ann.id" class="bim-list-item" style="flex-direction: column; align-items: flex-start">
                <div style="display: flex; justify-content: space-between; width: 100%; align-items: center">
                  <div style="font-size: 11px; font-weight: 500; cursor: pointer" @click="flyToAnnotation(ann)">{{ ann.title }}</div>
                  <ASpace size="small">
                    <ATag :color="priorityColors[ann.priority]" size="small">{{ ann.priority }}</ATag>
                    <ATag :color="statusColors[ann.status]" size="small">{{ ann.status }}</ATag>
                  </ASpace>
                </div>
                <div v-if="ann.description" style="font-size: 10px; color: #888; margin-top: 2px">{{ ann.description }}</div>
                <div v-if="ann.linked_entity_type" style="margin-top: 2px">
                  <ATag color="purple" size="small">{{ entityTypeLabels[ann.linked_entity_type] || ann.linked_entity_type }} #{{ ann.linked_entity_id }}</ATag>
                </div>
                <ASpace size="small" style="margin-top: 4px">
                  <AButton size="small" @click="flyToAnnotation(ann)">Fly To</AButton>
                  <AButton v-if="ann.status !== 'resolved'" size="small" type="primary" @click="resolveAnnotation(ann)">Resolve</AButton>
                  <AButton size="small" @click="openLinkEntityModal('annotation', ann.id)">Link</AButton>
                  <AButton size="small" danger @click="deleteAnnotation(ann)">Delete</AButton>
                </ASpace>
              </div>
            </div>
          </div>

          <!-- ═══════════ Phase 4C: IFC Type Colors Panel ═══════════ -->
          <div v-if="showColorsPanel" class="bim-right-panel bim-colors-panel" style="top: 12px; right: 170px">
            <div class="bim-panel-head">
              <strong>IFC Type Colors</strong>
              <AButton type="text" size="small" @click="showColorsPanel = false">X</AButton>
            </div>
            <div class="bim-colors-presets">
              <AButton size="small" :type="colorPresetsApplied === 'discipline' ? 'primary' : 'default'" @click="applyDisciplinePreset">By Discipline</AButton>
              <AButton size="small" @click="applyAllTypeColors">Apply All</AButton>
              <AButton size="small" danger @click="resetAllColors">Reset</AButton>
            </div>
            <div class="bim-panel-body">
              <div v-for="item in ifcTypeList" :key="item.type" class="bim-color-item">
                <input
                  type="color"
                  :value="item.color"
                  class="bim-color-swatch"
                  @input="onTypeColorChange(item.type, $event.target.value)"
                />
                <div class="bim-color-type-name">{{ formatIfcTypeName(item.type) }}</div>
                <AButton
                  size="small"
                  :type="item.visible ? 'default' : 'dashed'"
                  @click="toggleTypeVisibility(item.type)"
                >{{ item.visible ? 'Vis' : 'Hid' }}</AButton>
              </div>
            </div>
          </div>

          <!-- ═══════════ Phase 4F: Performance Panel ═══════════ -->
          <div v-if="showPerformancePanel" class="bim-right-panel bim-perf-panel" style="top: 12px; right: 170px">
            <div class="bim-panel-head">
              <strong>Performance</strong>
              <AButton type="text" size="small" @click="showPerformancePanel = false">X</AButton>
            </div>
            <div class="bim-panel-body">
              <!-- Stats -->
              <div class="bim-perf-stats">
                <div class="bim-perf-stat-item">
                  <span class="bim-perf-stat-label">FPS</span>
                  <span class="bim-perf-stat-value" :class="{ 'bim-fps-low': fpsCount < 20, 'bim-fps-ok': fpsCount >= 20 && fpsCount < 50, 'bim-fps-good': fpsCount >= 50 }">{{ fpsCount }}</span>
                </div>
                <div class="bim-perf-stat-item">
                  <span class="bim-perf-stat-label">Objects</span>
                  <span class="bim-perf-stat-value">{{ objectCount.toLocaleString() }}</span>
                </div>
              </div>

              <!-- Quick Presets -->
              <div class="bim-panel-section-title">Quick Presets</div>
              <div class="bim-perf-presets">
                <AButton size="small" :type="perfPreset === 'high' ? 'primary' : 'default'" @click="applyPerfPreset('high')">High Quality</AButton>
                <AButton size="small" :type="perfPreset === 'performance' ? 'primary' : 'default'" @click="applyPerfPreset('performance')">Performance</AButton>
                <AButton size="small" :type="perfPreset === 'wireframe' ? 'primary' : 'default'" @click="applyPerfPreset('wireframe')">Wireframe</AButton>
              </div>

              <!-- Individual Toggles -->
              <div class="bim-panel-section-title">Render Settings</div>
              <div class="bim-perf-toggle-list">
                <div class="bim-perf-toggle-item">
                  <span>SAO (Ambient Occlusion)</span>
                  <ASwitch :checked="perfSaoEnabled" size="small" @change="toggleSao" />
                </div>
                <div class="bim-perf-toggle-item">
                  <span>Edge Lines</span>
                  <ASwitch :checked="perfEdgesEnabled" size="small" @change="toggleEdges" />
                </div>
                <div class="bim-perf-toggle-item">
                  <span>PBR Rendering</span>
                  <ASwitch :checked="perfPbrEnabled" size="small" @change="togglePbr" />
                </div>
                <div class="bim-perf-toggle-item">
                  <span>Data Textures</span>
                  <ATag color="green" size="small">Enabled</ATag>
                </div>
              </div>

              <!-- Snapshot Settings -->
              <div class="bim-panel-section-title">Snapshot</div>
              <div class="bim-perf-toggle-item" style="padding: 6px 8px;">
                <span>Include watermark</span>
                <ASwitch :checked="snapshotIncludeWatermark" size="small" @change="(val) => snapshotIncludeWatermark = val" />
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

    <!-- ═══════════ Phase 3: LINK ENTITY MODAL ═══════════ -->
    <AModal
      v-model:open="linkEntityModalVisible"
      title="Link to Entity"
      :width="400"
      @ok="submitLinkEntity"
      okText="Link"
    >
      <AForm layout="vertical">
        <AFormItem label="Entity Type">
          <ASelect v-model:value="linkEntityForm.entity_type" style="width: 100%">
            <ASelectOption value="rfi">RFI</ASelectOption>
            <ASelectOption value="issue">Issue</ASelectOption>
            <ASelectOption value="clash">Clash</ASelectOption>
            <ASelectOption value="submittal">Submittal</ASelectOption>
          </ASelect>
        </AFormItem>
        <AFormItem label="Entity ID" required>
          <AInputNumber v-model:value="linkEntityForm.entity_id" style="width: 100%" placeholder="Enter entity ID" :min="1" />
        </AFormItem>
      </AForm>
    </AModal>
  </Page>
</template>
