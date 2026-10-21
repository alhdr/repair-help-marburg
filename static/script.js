/* ===========================================================================
   Marburg Repair Hub — home page map, search and service filtering
   Reads data injected by the index template as window.__DATA__
   =========================================================================== */
document.addEventListener("DOMContentLoaded", () => {
    const data = window.__DATA__ || {};
    const cafes = data.cafes || [];
    const lang = data.lang || "en";
    const S = data.strings || {};

    const mapEl = document.getElementById("map");
    const listEl = document.getElementById("cafeList");
    const detailsEl = document.getElementById("locationDetails");
    const searchEl = document.getElementById("locationSearch");
    const noResultsEl = document.getElementById("noResults");
    const heroInput = document.querySelector(".search-box input");
    const heroBtn = document.querySelector(".search-box button");
    const filterStatus = document.getElementById("filterStatus");
    const filterLabel = document.getElementById("filterLabel");
    const clearFilterBtn = document.getElementById("clearFilter");

    let query = "";
    let activeService = null;          // service slug or null

    /* --- Map setup --- */
    let map = null;
    let markerLayer = null;
    const markers = {};

    if (mapEl && window.L) {
        map = L.map("map").setView([50.807, 8.77], 13);
        L.tileLayer(
            "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            { attribution: "Tiles © Esri" }
        ).addTo(map);

        markerLayer = L.layerGroup().addTo(map);
        cafes.forEach(cafe => {
            if (cafe.lat == null || cafe.lng == null) return;
            const marker = L.marker([cafe.lat, cafe.lng]);
            marker.on("click", () => showDetails(cafe));
            markers[cafe.id] = marker;
        });
    }

    /* --- Filtering --- */
    function matches(cafe) {
        const okService = !activeService || (cafe.slugs || []).includes(activeService);
        const q = query.trim().toLowerCase();
        const hay = (
            cafe.name + " " +
            (cafe.services_en || []).join(" ") + " " +
            (cafe.services_de || []).join(" ")
        ).toLowerCase();
        const okQuery = q === "" || hay.includes(q);
        return okService && okQuery;
    }

    function render() {
        const visible = cafes.filter(matches);

        // List
        if (listEl) {
            listEl.innerHTML = "";
            visible.forEach(cafe => {
                const item = document.createElement("div");
                item.className = "cafe-item";
                item.textContent = cafe.name;
                item.addEventListener("click", () => {
                    showDetails(cafe);
                    if (map && cafe.lat != null) map.setView([cafe.lat, cafe.lng], 15);
                });
                listEl.appendChild(item);
            });
        }
        if (noResultsEl) noResultsEl.hidden = visible.length !== 0;

        // Markers
        if (markerLayer) {
            markerLayer.clearLayers();
            visible.forEach(cafe => {
                if (markers[cafe.id]) markerLayer.addLayer(markers[cafe.id]);
            });
        }

        // Active-filter banner
        if (filterStatus) {
            if (activeService) {
                const sample = cafes.find(c => (c.slugs || []).includes(activeService));
                const labelArr = sample
                    ? (lang === "de" ? sample.services_de : sample.services_en)
                    : [];
                const idx = sample ? sample.slugs.indexOf(activeService) : -1;
                filterLabel.textContent = (idx >= 0 ? labelArr[idx] : activeService);
                filterStatus.hidden = false;
            } else {
                filterStatus.hidden = true;
            }
        }
    }

    function showDetails(cafe) {
        if (!detailsEl) return;
        const svc = (lang === "de" ? cafe.services_de : cafe.services_en).join(", ");
        detailsEl.style.display = "block";
        detailsEl.innerHTML = `
            <h3>${cafe.name}</h3>
            <p><strong>📍 ${S.address}:</strong><br>${cafe.address || "—"}</p>
            <p><strong>🕒 ${S.hours}:</strong><br>${cafe.hours || "—"}</p>
            <p><strong>🔧 ${S.services}:</strong> ${svc || "—"}</p>
            <p><strong>💶 ${S.pricing}:</strong> ${cafe.pricing || "—"}</p>
            <p><strong>♿ ${S.access}:</strong> ${cafe.accessibility || "—"}</p>
            <p><strong>ℹ️ ${S.notes}:</strong> ${cafe.notes || "—"}</p>
            ${cafe.website
                ? `<p><strong>🌐 ${S.website}:</strong><br><a href="${cafe.website}" target="_blank" rel="noopener">${S.visit}</a></p>`
                : ""}
        `;
    }

    function scrollToMap() {
        const sec = document.getElementById("mapSection");
        if (sec) sec.scrollIntoView({ behavior: "smooth" });
    }

    /* --- Wiring --- */
    if (searchEl) {
        searchEl.addEventListener("input", e => { query = e.target.value; render(); });
    }

    if (heroBtn) {
        heroBtn.addEventListener("click", () => {
            query = heroInput ? heroInput.value : "";
            if (searchEl) searchEl.value = query;
            scrollToMap();
            render();
        });
    }

    document.querySelectorAll(".category-card").forEach(card => {
        card.style.cursor = "pointer";
        card.addEventListener("click", () => {
            const slug = card.getAttribute("data-service");
            activeService = (activeService === slug) ? null : slug;
            document.querySelectorAll(".category-card").forEach(c =>
                c.classList.toggle("active", c.getAttribute("data-service") === activeService));
            scrollToMap();
            render();
        });
    });

    if (clearFilterBtn) {
        clearFilterBtn.addEventListener("click", () => {
            activeService = null;
            document.querySelectorAll(".category-card").forEach(c => c.classList.remove("active"));
            render();
        });
    }

    render();   // initial: show the full default list + all markers
});
