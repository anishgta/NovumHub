/**
 * static/js/main.js
 * ==============================================================================
 * HACKREC INTERACTION SYSTEM: BOXY PAPER CRAFT & 3D ARTIFACT ENGINE
 * 1. Current X-Factor: "Neural Campus Strands" Interactive Canvas with physics
 * 2. Header Interactive 3D Model Viewport (Three.js OrbitControls, Wireframe, Upload .glb/.gltf)
 * 3. 3D Model Drag & Drop and Instant Server-Sync File Uploader
 * 4. Asynchronous AJAX Upvoting with CSRF Protection
 * 5. Dynamic Category Form Fields for Submission Builder
 * 6. Flash Message Dismissal & Mobile Navigation Drawer
 * ==============================================================================
 */

document.addEventListener("DOMContentLoaded", function () {
  console.log("[Hackrec] Boxy Paper & 3D Interaction Engine initialized.");

  // ============================================================================
  // 1. "NEURAL CAMPUS STRANDS" CANVAS CENTERPIECE (THE X-FACTOR)
  // ============================================================================
  const canvas = document.getElementById("hero-neural-canvas");
  if (canvas) {
    const ctx = canvas.getContext("2d");
    const container = canvas.parentElement;
    const telemetrySpan = document.getElementById("canvas-telemetry");
    const channelPills = document.querySelectorAll(".strand-pill");

    let width = 0;
    let height = 0;
    let dpr = window.devicePixelRatio || 1;
    let animationFrameId = null;

    // Palette configurations for ink lines on warm paper
    const channelPalettes = {
      all: {
        primary: "rgba(24, 23, 22, 0.40)",
        secondary: "rgba(136, 19, 55, 0.30)",
        nodes: ["#181716", "#881337", "#1d4ed8", "#047857"],
        strandWidth: 1.4,
        speed: 0.009
      },
      idea: {
        primary: "rgba(29, 78, 216, 0.65)",
        secondary: "rgba(29, 78, 216, 0.25)",
        nodes: ["#1d4ed8", "#2563eb", "#3b82f6", "#1e40af"],
        strandWidth: 1.6,
        speed: 0.012
      },
      research: {
        primary: "rgba(109, 40, 217, 0.65)",
        secondary: "rgba(109, 40, 217, 0.25)",
        nodes: ["#6d28d9", "#7c3aed", "#8b5cf6", "#5b21b6"],
        strandWidth: 1.6,
        speed: 0.010
      },
      correction: {
        primary: "rgba(190, 18, 60, 0.65)",
        secondary: "rgba(190, 18, 60, 0.25)",
        nodes: ["#be123c", "#e11d48", "#f43f5e", "#9f1239"],
        strandWidth: 1.6,
        speed: 0.014
      },
      showcase: {
        primary: "rgba(4, 120, 87, 0.65)",
        secondary: "rgba(4, 120, 87, 0.25)",
        nodes: ["#047857", "#059669", "#10b981", "#065f46"],
        strandWidth: 1.6,
        speed: 0.011
      }
    };

    let activeChannel = "all";
    let activePalette = channelPalettes.all;

    const mouse = {
      x: -1000,
      y: -1000,
      targetX: -1000,
      targetY: -1000,
      isHovering: false,
      radius: 190
    };

    const NODE_COUNT = 44;
    const STRAND_COUNT = 5;
    const nodes = [];
    let time = 0;

    function resizeCanvas() {
      if (!container) return;
      width = container.offsetWidth;
      height = container.offsetHeight;
      dpr = window.devicePixelRatio || 1;

      canvas.width = width * dpr;
      canvas.height = height * dpr;
      canvas.style.width = width + "px";
      canvas.style.height = height + "px";

      ctx.scale(dpr, dpr);
      initNodes();
    }

    function initNodes() {
      nodes.length = 0;
      for (let i = 0; i < NODE_COUNT; i++) {
        nodes.push({
          x: Math.random() * width,
          y: Math.random() * height,
          baseX: Math.random() * width,
          baseY: Math.random() * height,
          vx: (Math.random() - 0.5) * 0.45,
          vy: (Math.random() - 0.5) * 0.45,
          radius: Math.random() * 2.4 + 1.6,
          colorIdx: Math.floor(Math.random() * 4),
          pulseOffset: Math.random() * Math.PI * 2
        });
      }
    }

    const heroSection = document.getElementById("hero-section") || container;
    heroSection.addEventListener("mousemove", function (e) {
      const rect = container.getBoundingClientRect();
      mouse.targetX = e.clientX - rect.left;
      mouse.targetY = e.clientY - rect.top;
      mouse.isHovering = true;
    });

    heroSection.addEventListener("mouseleave", function () {
      mouse.isHovering = false;
      mouse.targetX = -1000;
      mouse.targetY = -1000;
    });

    heroSection.addEventListener("touchmove", function (e) {
      if (e.touches.length > 0) {
        const rect = container.getBoundingClientRect();
        mouse.targetX = e.touches[0].clientX - rect.left;
        mouse.targetY = e.touches[0].clientY - rect.top;
        mouse.isHovering = true;
      }
    }, { passive: true });

    heroSection.addEventListener("touchend", function () {
      mouse.isHovering = false;
    });

    channelPills.forEach(function (pill) {
      pill.addEventListener("click", function () {
        channelPills.forEach((p) => p.classList.remove("active"));
        pill.classList.add("active");

        const channel = pill.getAttribute("data-channel");
        activeChannel = channel;
        activePalette = channelPalettes[channel] || channelPalettes.all;

        if (telemetrySpan) {
          telemetrySpan.textContent = `MODE: ${channel.toUpperCase()} // NODES: ${NODE_COUNT} // VEL: ${(activePalette.speed * 100).toFixed(1)}`;
        }

        nodes.forEach(function (n) {
          n.vx += (Math.random() - 0.5) * 1.8;
          n.vy += (Math.random() - 0.5) * 1.8;
        });
      });
    });

    function renderCanvas() {
      ctx.clearRect(0, 0, width, height);

      mouse.x += (mouse.targetX - mouse.x) * 0.12;
      mouse.y += (mouse.targetY - mouse.y) * 0.12;
      time += activePalette.speed;

      // Draw Waving Ink Strands
      for (let s = 0; s < STRAND_COUNT; s++) {
        ctx.beginPath();
        const strandY = (height / (STRAND_COUNT + 1)) * (s + 1);
        const waveFreq = 0.003 + s * 0.0007;
        const waveAmp = 22 + s * 7;

        for (let x = 0; x <= width; x += 12) {
          let y = strandY + Math.sin(x * waveFreq + time * (s % 2 === 0 ? 1 : -1) + s) * waveAmp;

          if (mouse.isHovering) {
            const dx = x - mouse.x;
            const dy = y - mouse.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (dist < mouse.radius) {
              const force = (1 - dist / mouse.radius) * 32;
              y += (dy > 0 ? 1 : -1) * force;
            }
          }

          if (x === 0) {
            ctx.moveTo(x, y);
          } else {
            ctx.lineTo(x, y);
          }
        }

        ctx.strokeStyle = s === 0 ? activePalette.primary : activePalette.secondary;
        ctx.lineWidth = activePalette.strandWidth;
        ctx.stroke();
      }

      // Update and Draw Nodes
      for (let i = 0; i < nodes.length; i++) {
        const n = nodes[i];

        n.x += n.vx;
        n.y += n.vy;

        if (n.x < 0) n.x = width;
        if (n.x > width) n.x = 0;
        if (n.y < 0) n.y = height;
        if (n.y > height) n.y = 0;

        if (mouse.isHovering) {
          const dx = n.x - mouse.x;
          const dy = n.y - mouse.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < mouse.radius) {
            const push = (1 - dist / mouse.radius) * 1.5;
            n.x += (dx / dist) * push;
            n.y += (dy / dist) * push;
          }
        }

        // Draw node circle
        ctx.beginPath();
        const pulse = Math.sin(time * 2 + n.pulseOffset) * 0.6;
        ctx.arc(n.x, n.y, Math.max(1, n.radius + pulse), 0, Math.PI * 2);
        ctx.fillStyle = activePalette.nodes[n.colorIdx % activePalette.nodes.length];
        ctx.fill();

        // Connect nearby nodes with ink hairpins
        for (let j = i + 1; j < nodes.length; j++) {
          const n2 = nodes[j];
          const dx = n.x - n2.x;
          const dy = n.y - n2.y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < 110) {
            ctx.beginPath();
            ctx.moveTo(n.x, n.y);
            ctx.lineTo(n2.x, n2.y);
            const alpha = (1 - dist / 110) * 0.22;
            ctx.strokeStyle = `rgba(24, 23, 22, ${alpha})`;
            ctx.lineWidth = 0.75;
            ctx.stroke();
          }
        }
      }

      animationFrameId = requestAnimationFrame(renderCanvas);
    }

    resizeCanvas();
    window.addEventListener("resize", resizeCanvas);
    renderCanvas();
  }


  // ============================================================================
  // 2. HEADER INTERACTIVE 3D MODEL VIEWPORT & UPLOAD SYSTEM
  // ============================================================================
  const viewport3D = document.getElementById("header-3d-viewport");
  const canvas3D = document.getElementById("header-3d-canvas");

  if (viewport3D && canvas3D && typeof THREE !== "undefined") {
    let scene, camera, renderer, controls;
    let currentModelGroup = new THREE.Group();
    let defaultOrigamiMesh = null;
    let defaultEdgesMesh = null;
    let isWireframeActive = false;
    let isAutoRotateActive = true;
    let animationId = null;

    const loaderText = document.getElementById("header-3d-loader-text");
    const loaderElem = document.getElementById("header-3d-loader");
    const modelBadge = document.getElementById("active-model-name");
    const dropzone = document.getElementById("header-3d-dropzone");
    const uploadInput = document.getElementById("model-upload-input");
    const btnUpload = document.getElementById("btn-upload-3d-model");
    const btnReset = document.getElementById("btn-reset-3d-model");
    const btnAutoRotate = document.getElementById("btn-3d-autorotate");
    const btnWireframe = document.getElementById("btn-3d-wireframe");
    const btnRecenter = document.getElementById("btn-3d-recenter");
    const autorotateStatus = document.getElementById("autorotate-status");
    const wireframeStatus = document.getElementById("wireframe-status");
    const statusStrip = document.getElementById("model-status-strip");
    const statusMsg = document.getElementById("status-msg");
    const statusDismiss = document.getElementById("status-dismiss");

    function showStatus(text, isError = false) {
      if (!statusStrip || !statusMsg) return;
      statusMsg.textContent = text;
      statusStrip.style.display = "flex";
      statusStrip.classList.toggle("status-error", isError);
      setTimeout(() => {
        if (statusStrip) statusStrip.style.display = "none";
      }, 7000);
    }

    if (statusDismiss) {
      statusDismiss.addEventListener("click", () => {
        if (statusStrip) statusStrip.style.display = "none";
      });
    }

    function initThreeScene() {
      const width = viewport3D.clientWidth || 480;
      const height = viewport3D.clientHeight || 340;

      scene = new THREE.Scene();
      scene.add(currentModelGroup);

      camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
      camera.position.set(0, 1.2, 3.8);

      renderer = new THREE.WebGLRenderer({
        canvas: canvas3D,
        antialias: true,
        alpha: true
      });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
      renderer.setSize(width, height);
      renderer.shadowMap.enabled = true;
      renderer.toneMapping = THREE.ACESFilmicToneMapping;
      renderer.toneMappingExposure = 1.1;

      // Orbit Controls
      controls = new THREE.OrbitControls(camera, renderer.domElement);
      controls.enableDamping = true;
      controls.dampingFactor = 0.06;
      controls.autoRotate = true;
      controls.autoRotateSpeed = 1.4;
      controls.maxPolarAngle = Math.PI / 2 + 0.35;
      controls.minDistance = 1.0;
      controls.maxDistance = 12.0;

      // Warm paper-themed studio lighting
      const ambientLight = new THREE.AmbientLight(0xfff7ed, 1.4);
      scene.add(ambientLight);

      const dirLight1 = new THREE.DirectionalLight(0xffffff, 1.5);
      dirLight1.position.set(5, 8, 6);
      scene.add(dirLight1);

      const dirLight2 = new THREE.DirectionalLight(0x881337, 0.7);
      dirLight2.position.set(-5, -3, -4);
      scene.add(dirLight2);

      const topLight = new THREE.DirectionalLight(0x1d4ed8, 0.4);
      topLight.position.set(0, 8, -5);
      scene.add(topLight);

      // Build Procedural Origami Paper Polyhedron
      buildDefaultOrigamiModel();

      // Check for active custom model from server
      const initialUrl = viewport3D.getAttribute("data-active-model-url");
      const initialName = viewport3D.getAttribute("data-active-model-name");
      if (initialUrl && initialUrl.trim() !== "") {
        loadGLTFFromUrl(initialUrl, initialName || "Custom 3D Model");
      }

      window.addEventListener("resize", onWindowResize);
      animate3D();
    }

    function buildDefaultOrigamiModel() {
      // Clear current model group
      while (currentModelGroup.children.length > 0) {
        currentModelGroup.remove(currentModelGroup.children[0]);
      }

      // Create an origami folded polyhedron (Faceted Icosahedron with paper texture feel)
      const geometry = new THREE.IcosahedronGeometry(1.2, 0);
      
      const paperMaterial = new THREE.MeshStandardMaterial({
        color: 0xfcfaf4,
        roughness: 0.75,
        metalness: 0.05,
        flatShading: true
      });

      defaultOrigamiMesh = new THREE.Mesh(geometry, paperMaterial);
      currentModelGroup.add(defaultOrigamiMesh);

      // Sharp ink wireframe edge lines
      const edges = new THREE.EdgesGeometry(geometry);
      const lineMaterial = new THREE.LineBasicMaterial({
        color: 0x181716,
        linewidth: 2
      });
      defaultEdgesMesh = new THREE.LineSegments(edges, lineMaterial);
      currentModelGroup.add(defaultEdgesMesh);

      // Center model
      currentModelGroup.position.set(0, 0, 0);
      camera.position.set(0, 0.8, 3.8);
      controls.target.set(0, 0, 0);
      controls.update();

      if (modelBadge) {
        modelBadge.textContent = "Active: Origami Folded Gem";
      }
    }

    function animate3D() {
      animationId = requestAnimationFrame(animate3D);

      controls.update();

      // Subtle breathing floating motion if using default origami model
      if (defaultOrigamiMesh && currentModelGroup.children.includes(defaultOrigamiMesh)) {
        const timeNow = performance.now() * 0.001;
        defaultOrigamiMesh.rotation.y = timeNow * 0.15;
        if (defaultEdgesMesh) {
          defaultEdgesMesh.rotation.y = timeNow * 0.15;
        }
      }

      renderer.render(scene, camera);
    }

    function onWindowResize() {
      if (!viewport3D || !camera || !renderer) return;
      const width = viewport3D.clientWidth;
      const height = viewport3D.clientHeight;
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height);
    }

    // Load GLTF / GLB model file
    function loadGLTFFromUrl(modelUrl, displayName = "Uploaded 3D Model") {
      if (typeof THREE.GLTFLoader === "undefined") {
        console.error("GLTFLoader not loaded!");
        showStatus("Error: 3D model loader not available", true);
        return;
      }

      if (loaderElem) {
        loaderElem.style.display = "flex";
        if (loaderText) loaderText.textContent = `Loading ${displayName}...`;
      }

      const loader = new THREE.GLTFLoader();
      loader.load(
        modelUrl,
        function (gltf) {
          // Clear previous model
          while (currentModelGroup.children.length > 0) {
            currentModelGroup.remove(currentModelGroup.children[0]);
          }

          const model = gltf.scene;

          // Compute bounding box to center & auto-scale
          const box = new THREE.Box3().setFromObject(model);
          const size = box.getSize(new THREE.Vector3());
          const center = box.getCenter(new THREE.Vector3());

          // Re-center model at origin
          model.position.x = -center.x;
          model.position.y = -center.y;
          model.position.z = -center.z;

          // Scale model so largest dimension fits ~2.2 units
          const maxDim = Math.max(size.x, size.y, size.z);
          if (maxDim > 0) {
            const scale = 2.2 / maxDim;
            model.scale.set(scale, scale, scale);
          }

          // Apply paper shadow & wireframe settings
          model.traverse(function (child) {
            if (child.isMesh) {
              child.castShadow = true;
              child.receiveShadow = true;
              if (child.material) {
                child.material.wireframe = isWireframeActive;
                if (child.material.roughness !== undefined) {
                  child.material.roughness = Math.max(child.material.roughness, 0.4);
                }
              }
            }
          });

          currentModelGroup.add(model);
          defaultOrigamiMesh = null;
          defaultEdgesMesh = null;

          // Adjust camera
          camera.position.set(0, 1.0, 3.8);
          controls.target.set(0, 0, 0);
          controls.update();

          if (loaderElem) loaderElem.style.display = "none";
          if (modelBadge) modelBadge.textContent = `Active: ${displayName}`;
          if (btnReset) btnReset.style.display = "inline-flex";

          showStatus(`3D model '${displayName}' successfully activated!`);
        },
        function (xhr) {
          if (loaderText && xhr.total > 0) {
            const percent = Math.round((xhr.loaded / xhr.total) * 100);
            loaderText.textContent = `Loading ${percent}%...`;
          }
        },
        function (error) {
          console.error("Error loading GLTF model:", error);
          if (loaderElem) loaderElem.style.display = "none";
          showStatus("Could not load 3D file. Please check GLB/GLTF format.", true);
          buildDefaultOrigamiModel();
        }
      );
    }

    // Upload & Handle 3D File (Instant client-preview + background server sync)
    function handleModelUpload(file) {
      if (!file) return;

      const filename = file.name || "model.glb";
      const ext = filename.toLowerCase().slice(filename.lastIndexOf("."));

      if (ext !== ".glb" && ext !== ".gltf") {
        showStatus("Invalid file format. Please upload a .glb or .gltf 3D model.", true);
        return;
      }

      showStatus(`Loading 3D model '${filename}'...`);

      // 1. Instant Client-Side Preview via ObjectURL
      const localUrl = URL.createObjectURL(file);
      loadGLTFFromUrl(localUrl, filename);

      // 2. Server Upload for Persistence
      const formData = new FormData();
      formData.append("model_file", file);

      const csrfMeta = document.querySelector('meta[name="csrf-token"]');
      const csrfToken = csrfMeta ? csrfMeta.getAttribute("content") : "";

      fetch("/api/upload-header-model", {
        method: "POST",
        headers: csrfToken ? { "X-CSRFToken": csrfToken } : {},
        body: formData
      })
        .then((res) => res.json())
        .then((data) => {
          if (data.success) {
            showStatus(`"${filename}" saved and activated as default 3D model!`);
            if (btnReset) btnReset.style.display = "inline-flex";
          } else {
            console.warn("Upload response issue:", data);
          }
        })
        .catch((err) => {
          console.error("Server upload sync error:", err);
          // Preview is still running locally!
          showStatus(`Loaded in preview. (Server sync offline: ${err.message})`, true);
        });
    }

    // Trigger Upload Picker
    if (btnUpload && uploadInput) {
      btnUpload.addEventListener("click", () => uploadInput.click());
      uploadInput.addEventListener("change", (e) => {
        if (e.target.files && e.target.files[0]) {
          handleModelUpload(e.target.files[0]);
        }
      });
    }

    // Drag and Drop support over 3D viewport
    viewport3D.addEventListener("dragover", (e) => {
      e.preventDefault();
      e.stopPropagation();
      if (dropzone) dropzone.style.display = "flex";
    });

    viewport3D.addEventListener("dragleave", (e) => {
      e.preventDefault();
      e.stopPropagation();
      if (dropzone && !viewport3D.contains(e.relatedTarget)) {
        dropzone.style.display = "none";
      }
    });

    viewport3D.addEventListener("drop", (e) => {
      e.preventDefault();
      e.stopPropagation();
      if (dropzone) dropzone.style.display = "none";

      if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        handleModelUpload(e.dataTransfer.files[0]);
      }
    });

    // Reset to Default Origami Model
    if (btnReset) {
      btnReset.addEventListener("click", () => {
        showStatus("Resetting to default origami model...");
        fetch("/api/reset-header-model", { method: "POST" })
          .then((res) => res.json())
          .then(() => {
            buildDefaultOrigamiModel();
            btnReset.style.display = "none";
            showStatus("Reset to default origami 3D model.");
          })
          .catch(() => {
            buildDefaultOrigamiModel();
            btnReset.style.display = "none";
          });
      });
    }

    // Auto-Rotate Toggle
    if (btnAutoRotate && autorotateStatus) {
      btnAutoRotate.addEventListener("click", () => {
        isAutoRotateActive = !isAutoRotateActive;
        controls.autoRotate = isAutoRotateActive;
        autorotateStatus.textContent = isAutoRotateActive ? "ON" : "OFF";
        btnAutoRotate.classList.toggle("active", isAutoRotateActive);
      });
    }

    // Wireframe Toggle
    if (btnWireframe && wireframeStatus) {
      btnWireframe.addEventListener("click", () => {
        isWireframeActive = !isWireframeActive;
        wireframeStatus.textContent = isWireframeActive ? "ON" : "OFF";
        btnWireframe.classList.toggle("active", isWireframeActive);

        currentModelGroup.traverse((child) => {
          if (child.isMesh && child.material) {
            child.material.wireframe = isWireframeActive;
          }
        });
      });
    }

    // Recenter View
    if (btnRecenter) {
      btnRecenter.addEventListener("click", () => {
        camera.position.set(0, 1.2, 3.8);
        controls.target.set(0, 0, 0);
        controls.update();
      });
    }

    // Initialize 3D Engine
    initThreeScene();
  }


  // ============================================================================
  // 3. ASYNC UPVOTE BUTTON HANDLER (BOXY PAPER BUTTONS)
  // ============================================================================
  const upvoteButtons = document.querySelectorAll(".ajax-upvote-btn");

  upvoteButtons.forEach(function (button) {
    button.addEventListener("click", async function (event) {
      event.preventDefault();
      event.stopPropagation();

      const submissionId = button.getAttribute("data-id");
      const countSpan = button.querySelector(".upvote-count");

      const csrfMeta = document.querySelector('meta[name="csrf-token"]');
      const csrfToken = csrfMeta ? csrfMeta.getAttribute("content") : "";

      try {
        const response = await fetch(`/submissions/${submissionId}/upvote`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken
          }
        });

        if (response.status === 401) {
          window.location.href = "/login?next=" + encodeURIComponent(window.location.pathname);
          return;
        }

        const data = await response.json();

        if (data.success) {
          if (countSpan) {
            countSpan.textContent = data.upvote_count;
          }

          if (data.upvoted) {
            button.classList.add("upvoted");
          } else {
            button.classList.remove("upvoted");
          }
        } else if (data.message) {
          alert(data.message);
        }
      } catch (error) {
        console.error("Error toggling upvote:", error);
      }
    });
  });


  // ============================================================================
  // 4. DYNAMIC CATEGORY FIELDS ON SUBMISSION FORM
  // ============================================================================
  const categorySelect = document.getElementById("category-selector");

  if (categorySelect) {
    function updateCategoryFields() {
      const selectedValue = categorySelect.value;

      const ideaGroup = document.getElementById("group-idea");
      const researchGroup = document.getElementById("group-research");
      const correctionGroup = document.getElementById("group-correction");
      const infraGroup = document.getElementById("group-infrastructure");

      if (ideaGroup) ideaGroup.style.display = "none";
      if (researchGroup) researchGroup.style.display = "none";
      if (correctionGroup) correctionGroup.style.display = "none";
      if (infraGroup) infraGroup.style.display = "none";

      if (selectedValue === "idea" && ideaGroup) {
        ideaGroup.style.display = "block";
      } else if (selectedValue === "research" && researchGroup) {
        researchGroup.style.display = "block";
      } else if (selectedValue === "correction" && correctionGroup) {
        correctionGroup.style.display = "block";
      } else if (selectedValue === "infrastructure" && infraGroup) {
        infraGroup.style.display = "block";
      }
    }

    updateCategoryFields();
    categorySelect.addEventListener("change", updateCategoryFields);
  }


  // ============================================================================
  // 5. AUTO-DISMISS FLASH MESSAGES
  // ============================================================================
  const alerts = document.querySelectorAll(".alert, .flash-message");
  if (alerts.length > 0) {
    setTimeout(function () {
      alerts.forEach(function (alert) {
        alert.style.transition = "opacity 0.5s ease, transform 0.5s ease";
        alert.style.opacity = "0";
        alert.style.transform = "translateY(-10px)";
        setTimeout(() => alert.remove(), 500);
      });
    }, 6000);
  }


  // ============================================================================
  // 6. MOBILE NAVIGATION MENU TOGGLE
  // ============================================================================
  const navToggle = document.getElementById("nav-toggle");
  const navMenu = document.getElementById("nav-menu");

  if (navToggle && navMenu) {
    navToggle.addEventListener("click", function () {
      const isExpanded = navToggle.getAttribute("aria-expanded") === "true";
      navToggle.setAttribute("aria-expanded", !isExpanded);
      navMenu.classList.toggle("is-active");
    });

    document.addEventListener("click", function (event) {
      if (!navToggle.contains(event.target) && !navMenu.contains(event.target)) {
        navMenu.classList.remove("is-active");
        navToggle.setAttribute("aria-expanded", "false");
      }
    });
  }


  // ============================================================================
  // 7. PERSISTENT LOOPED BACKGROUND MUSIC CONTROLLER (LOFI SYNTH)
  // ============================================================================
  const bgAudio = document.getElementById("site-bg-music");
  const musicToggleBtn = document.getElementById("music-toggle-btn");
  const musicMuteBtn = document.getElementById("music-mute-btn");
  const musicVolSlider = document.getElementById("music-volume-slider");
  const musicVolVal = document.getElementById("music-vol-val");
  const musicStatusText = document.getElementById("music-status-text");
  const volIconActive = document.getElementById("music-vol-icon-active");
  const volIconMuted = document.getElementById("music-vol-icon-muted");

  if (bgAudio && musicToggleBtn) {
    const STORAGE_KEY_PLAYING = "novum_bg_music_playing";
    const STORAGE_KEY_TIME = "novum_bg_music_time";
    const STORAGE_KEY_VOL = "novum_bg_music_volume";
    const STORAGE_KEY_MUTED = "novum_bg_music_muted";

    // Restore saved volume (default to 0.35 for pleasant background ambiance)
    const savedVol = parseFloat(localStorage.getItem(STORAGE_KEY_VOL) || "0.35");
    bgAudio.volume = isNaN(savedVol) ? 0.35 : Math.max(0, Math.min(1, savedVol));
    if (musicVolSlider) musicVolSlider.value = Math.round(bgAudio.volume * 100);
    if (musicVolVal) musicVolVal.textContent = Math.round(bgAudio.volume * 100) + "%";

    // Restore saved muted state
    const savedMuted = localStorage.getItem(STORAGE_KEY_MUTED) === "true";
    bgAudio.muted = savedMuted;
    updateMuteUI(savedMuted);

    // Restore playback timestamp across page transitions
    const savedTime = parseFloat(sessionStorage.getItem(STORAGE_KEY_TIME) || "0");
    if (!isNaN(savedTime) && savedTime > 0) {
      bgAudio.currentTime = savedTime;
    }

    function updatePlayUI(isPlaying) {
      if (isPlaying) {
        musicToggleBtn.classList.add("is-playing");
        musicToggleBtn.setAttribute("aria-pressed", "true");
        if (musicStatusText) musicStatusText.innerHTML = "Playing &bull; Click to Pause";
      } else {
        musicToggleBtn.classList.remove("is-playing");
        musicToggleBtn.setAttribute("aria-pressed", "false");
        if (musicStatusText) musicStatusText.innerHTML = "Paused &bull; Click to Play";
      }
    }

    function updateMuteUI(isMuted) {
      if (volIconActive && volIconMuted) {
        if (isMuted) {
          volIconActive.style.display = "none";
          volIconMuted.style.display = "inline";
        } else {
          volIconActive.style.display = "inline";
          volIconMuted.style.display = "none";
        }
      }
    }

    function playAudio() {
      const playPromise = bgAudio.play();
      if (playPromise !== undefined) {
        playPromise
          .then(() => {
            updatePlayUI(true);
            localStorage.setItem(STORAGE_KEY_PLAYING, "true");
          })
          .catch((err) => {
            console.log("[Music] Autoplay policy prevented immediate playback:", err);
            updatePlayUI(false);
          });
      }
    }

    function pauseAudio() {
      bgAudio.pause();
      updatePlayUI(false);
      localStorage.setItem(STORAGE_KEY_PLAYING, "false");
    }

    // Toggle button click
    musicToggleBtn.addEventListener("click", function (e) {
      e.stopPropagation();
      if (bgAudio.paused) {
        playAudio();
      } else {
        pauseAudio();
      }
    });

    // Volume Slider
    if (musicVolSlider) {
      musicVolSlider.addEventListener("input", function () {
        const vol = parseInt(this.value, 10) / 100;
        bgAudio.volume = vol;
        if (musicVolVal) musicVolVal.textContent = this.value + "%";
        localStorage.setItem(STORAGE_KEY_VOL, vol.toString());
        if (bgAudio.muted && vol > 0) {
          bgAudio.muted = false;
          updateMuteUI(false);
          localStorage.setItem(STORAGE_KEY_MUTED, "false");
        }
      });
    }

    // Mute button
    if (musicMuteBtn) {
      musicMuteBtn.addEventListener("click", function (e) {
        e.stopPropagation();
        bgAudio.muted = !bgAudio.muted;
        updateMuteUI(bgAudio.muted);
        localStorage.setItem(STORAGE_KEY_MUTED, bgAudio.muted.toString());
      });
    }

    // Continuously save current playback time so page navigations resume seamlessly
    bgAudio.addEventListener("timeupdate", function () {
      if (!bgAudio.paused && bgAudio.currentTime > 0) {
        sessionStorage.setItem(STORAGE_KEY_TIME, bgAudio.currentTime.toString());
      }
    });

    window.addEventListener("beforeunload", function () {
      if (bgAudio.currentTime > 0) {
        sessionStorage.setItem(STORAGE_KEY_TIME, bgAudio.currentTime.toString());
      }
    });

    // Handle seamless session persistence across navigations
    const wasPlaying = localStorage.getItem(STORAGE_KEY_PLAYING) === "true";
    if (wasPlaying) {
      const promise = bgAudio.play();
      if (promise !== undefined) {
        promise
          .then(() => {
            updatePlayUI(true);
          })
          .catch(() => {
            const unlockAudio = function () {
              if (localStorage.getItem(STORAGE_KEY_PLAYING) === "true" && bgAudio.paused) {
                bgAudio.play().then(() => updatePlayUI(true)).catch(() => {});
              }
              document.removeEventListener("pointerdown", unlockAudio);
              document.removeEventListener("keydown", unlockAudio);
            };
            document.addEventListener("pointerdown", unlockAudio, { once: true });
            document.addEventListener("keydown", unlockAudio, { once: true });
          });
      }
    }
  }
});

