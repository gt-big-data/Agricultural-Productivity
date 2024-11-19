import { ControlPosition, useMap, useMapsLibrary } from "@vis.gl/react-google-maps";
import { useContext, useEffect } from "react";
import { MapContext } from "../App";

export default function useDrawingManager() {
  const [drawingManager, setDrawingManager, infoWindow, setInfoWindow, markerPosition, setMarkerPosition] = useContext(MapContext);
  const map = useMap();
  const drawing = useMapsLibrary("drawing");
  const google = window.google;

  useEffect(() => {
    if (!map || !drawing) return;

    const drawingManager = new drawing.DrawingManager({
      map: map,
      drawingMode: drawing.OverlayType.RECTANGLE,
      drawingControl: true,
      drawingControlOptions: {
        position: ControlPosition.TOP_CENTER,
        drawingModes: ['rectangle'],
      },
      rectangleOptions: {
        fillColor: '#000000',
        fillOpacity: 0.5,
        strokeWeight: 1,
        clickable: false,
        editable: false,
        zIndex: 1,
      },
    });

    setDrawingManager(drawingManager);

    google.maps.event.addListener(drawingManager, 'rectanglecomplete', function (rectangle) {
      drawingManager.setMap(null);
      const coordinates = rectangle.getBounds(); // Get bounds of the rectangle

      // Set marker position
      setMarkerPosition(coordinates);

      // Extract the bounds
      const { south, west, north, east } = coordinates.toJSON();

      // Fetch image for the rectangle bounds
      fetch(`http://128.61.104.217:8081/segment?south=${south}&west=${west}&north=${north}&east=${east}`)
        .then(response => response.blob())
        .then(blob => {
          const srcImage = URL.createObjectURL(blob);

          // Create a custom overlay after the image is loaded
          class USGSOverlay extends google.maps.OverlayView {
            constructor(bounds, image) {
              super();
              this.bounds_ = bounds;
              this.image_ = image;
              this.div_ = null;
            }

            onAdd() {
              this.div_ = document.createElement("div");
              this.div_.style.borderStyle = "none";
              this.div_.style.borderWidth = "0px";
              this.div_.style.position = "absolute";

              const img = document.createElement("img");
              img.src = this.image_;
              img.style.width = "100%";
              img.style.height = "100%";
              img.style.position = "absolute";
              this.div_.appendChild(img);

              const panes = this.getPanes();
              panes.overlayLayer.appendChild(this.div_);
            }

            draw() {
              const overlayProjection = this.getProjection();
              const sw = overlayProjection.fromLatLngToDivPixel(this.bounds_.getSouthWest());
              const ne = overlayProjection.fromLatLngToDivPixel(this.bounds_.getNorthEast());

              if (this.div_) {
                this.div_.style.left = sw.x + "px";
                this.div_.style.top = ne.y + "px";
                this.div_.style.width = ne.x - sw.x + "px";
                this.div_.style.height = sw.y - ne.y + "px";
              }
            }

            onRemove() {
              if (this.div_) {
                this.div_.parentNode.removeChild(this.div_);
                this.div_ = null;
              }
            }
          }

          // Instantiate the overlay after the image is ready
          const overlay = new USGSOverlay(coordinates, srcImage);
          overlay.setMap(map);
        });

    });

    return () => {
      drawingManager.setMap(null); // Cleanup
    };
  }, [drawing, map]);
}