import { ControlPosition, useMap, useMapsLibrary } from "@vis.gl/react-google-maps";
import { useContext, useEffect, useState } from "react"
import { MapContext } from "../App";

export default function useDrawingManager() {
    const [drawingManager, setDrawingManager] = useContext(MapContext);

    const map = useMap();
    const drawing = useMapsLibrary("drawing");


    useEffect(() => {
        if (!map || !drawing) return;

        const drawingManager = new drawing.DrawingManager({
            map: map,
            drawingMode: drawing.OverlayType.POLYGON,
            drawingControl: true,
            drawingControlOptions: {
                position: ControlPosition.TOP_CENTER,
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