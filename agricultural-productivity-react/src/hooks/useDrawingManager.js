import { useMap, useMapsLibrary } from "@vis.gl/react-google-maps";
import { useEffect, useState } from "react"

export default function useDrawingManager() {
    const [drawingManager, setDrawingManager] = useState();

    const map = useMap();
    const drawing = useMapsLibrary("drawing");

    useEffect(() => {
        if (!map || !drawing) return;

        const drawingManager = new google.maps.drawing.DrawingManager({
            map: map,
            drawingMode: google.maps.drawing.OverlayType.POLYGON,
            drawingControl: true,
            drawingControlOptions: {
                position: google.maps.ControlPosition.TOP_CENTER,
                drawingModes: ['polygon'],
            },
            polygonOptions: {
                fillColor: '#FF0000',
                fillOpacity: 0.5,
                strokeWeight: 1,
                clickable: false,
                editable: false,
                zIndex: 1,
            },
        });

        setDrawingManager(drawingManager);

        return () => {
            drawingManager.setMap(null);
        }
    }, [drawing, map])
}