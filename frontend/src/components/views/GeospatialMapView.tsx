"use client";

import React, { useEffect, useRef, useState } from "react";
import { AttributionControl, Map as MapLibreMap, Marker, NavigationControl } from "maplibre-gl";
import { MapPin, Crosshair, ArrowRight, Navigation } from "lucide-react";

interface CaseLocation {
  id: string;
  name: string;
  category: "recovery" | "police_station" | "hospital" | "forensic_lab";
  coords: [number, number];
  address: string;
  details: string;
  color: string;
}

const CASE_LOCATIONS: CaseLocation[] = [
  { id: "loc-recovery", name: "Recovery Spot · Munirka Village", category: "recovery", coords: [77.1738, 28.5562], address: "House No. 42, Munirka Village, South West Delhi", details: "Seizure Memo under Sec 100/102 CrPC. Articles seized: iPhone 15, Dell Laptop, Cash Rs. 60,000.", color: "#A66A00" },
  { id: "loc-ps", name: "Police Station · Vasant Vihar", category: "police_station", coords: [77.1582, 28.5605], address: "Nelson Mandela Marg, Vasant Vihar, New Delhi", details: "Registration of FIR 184/2026 and arrest-memo activity associated with the current case record.", color: "#0F766E" },
  { id: "loc-hospital", name: "Medico-Legal Center · Safdarjung", category: "hospital", coords: [77.2069, 28.5684], address: "Ring Road, opposite AIIMS, Safdarjung Enclave, New Delhi", details: "Medical examination record referenced by the current case evidence.", color: "#C73E46" },
  { id: "loc-fsl", name: "FSL · Rohini", category: "forensic_lab", coords: [77.1332, 28.7166], address: "FSL Campus, Sector 14, Rohini, Delhi", details: "Forensic report and electronic-evidence certificate associated with the case.", color: "#5B5BC7" },
];

export const GeospatialMapView: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const [selectedLoc, setSelectedLoc] = useState(CASE_LOCATIONS[0]);

  useEffect(() => {
    if (!containerRef.current) return;
    const map = new MapLibreMap({
      container: containerRef.current,
      style: {
        version: 8,
        sources: {
          osm: {
            type: "raster",
            tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
            tileSize: 256,
            attribution: "© OpenStreetMap contributors",
          },
        },
        layers: [{ id: "osm", type: "raster", source: "osm", minzoom: 0, maxzoom: 19 }],
      },
      center: [77.178, 28.585],
      zoom: 11.4,
      attributionControl: false,
    });

    map.addControl(new NavigationControl({ showCompass: true }), "top-right");
    map.addControl(new AttributionControl({ compact: true }), "bottom-right");

    map.on("load", () => {
      CASE_LOCATIONS.forEach((location) => {
        const element = document.createElement("button");
        element.type = "button";
        element.setAttribute("aria-label", `Focus map on ${location.name}`);
        element.title = `${location.name} — focus map and inspect evidence`;
        element.style.width = "28px";
        element.style.height = "28px";
        element.style.borderRadius = "50%";
        element.style.background = "#FFFFFF";
        element.style.border = `2px solid ${location.color}`;
        element.style.display = "grid";
        element.style.placeItems = "center";
        element.style.cursor = "pointer";
        element.style.boxShadow = "0 2px 10px rgba(23,32,38,.16)";
        element.innerHTML = `<span style="width:8px;height:8px;border-radius:50%;background:${location.color};display:block"></span>`;
        element.addEventListener("click", () => {
          setSelectedLoc(location);
          map.flyTo({ center: location.coords, zoom: 13.5, speed: 1.1 });
        });
        new Marker({ element }).setLngLat(location.coords).addTo(map);
      });
    });
    mapRef.current = map;
    return () => map.remove();
  }, []);

  const selectLocation = (location: CaseLocation) => {
    setSelectedLoc(location);
    mapRef.current?.flyTo({ center: location.coords, zoom: 13.5, speed: 1.1 });
  };

  const fitCase = () => mapRef.current?.fitBounds([[77.12, 28.53], [77.23, 28.73]], { padding: 70, duration: 600 });

  return (
    <div className="sanket-locations">
      <div className="sanket-locations__toolbar">
        <div><span className="sanket-card__meta">Location evidence</span><strong>4 places referenced by the case</strong></div>
        <button type="button" className="sanket-button" onClick={fitCase} data-tooltip="Fit all case locations into the map" title="Fit all case locations"><Crosshair size={14} /> Fit case</button>
      </div>
      <div className="sanket-locations__body">
        <div ref={containerRef} className="sanket-locations__map" aria-label="OpenStreetMap case location map" />
        <aside className="sanket-locations__panel">
          <div className="sanket-locations__panel-head"><div><span className="sanket-card__meta">Case locations</span><h3>{CASE_LOCATIONS.length} identified sites</h3></div><MapPin size={16} color="var(--teal)" /></div>
          <div className="sanket-location-list">
            {CASE_LOCATIONS.map((location) => {
              const active = location.id === selectedLoc.id;
              return <button key={location.id} type="button" className={`sanket-location-row ${active ? "is-active" : ""}`} onClick={() => selectLocation(location)} title={`Focus the map on ${location.name} and review its evidence`}><span className="sanket-location-dot" style={{ background: location.color }} /><span><strong>{location.name}</strong><small>{location.address}</small></span><ArrowRight size={12} /></button>;
            })}
          </div>
          <div className="sanket-location-detail">
            <div className="sanket-location-detail__meta"><span><Navigation size={11} /> {selectedLoc.coords[1].toFixed(4)}°N, {selectedLoc.coords[0].toFixed(4)}°E</span><span>{selectedLoc.category.replace("_", " ")}</span></div>
            <h4>{selectedLoc.name}</h4>
            <p>{selectedLoc.details}</p>
          </div>
          <div className="sanket-osm-attribution">Map data © OpenStreetMap contributors</div>
        </aside>
      </div>
    </div>
  );
};
