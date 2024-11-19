import { useContext, useEffect, useState } from "react"
import { MapContext } from "../App";
import { useMap, useMapsLibrary } from "@vis.gl/react-google-maps";

export default function useInfoWindow() {
    const [drawingManager, setDrawingManager, infoWindow, setInfoWindow, markerPosition, setMarkerPosition] = useContext(MapContext);
    const map = useMap();
    const drawing = useMapsLibrary("drawing");
    const google = window.google;

    const contentString =
    '<div id="content">' +
    '<div id="siteNotice">' +
    "</div>" +
    '<h1 id="firstHeading" class="firstHeading">Iowa</h1>' +
    '<div id="bodyContent">' +
    "<p><b>This area has corn and wheat </b> .</p>" +
    "</div>" +
    "</div>";

    useEffect(() => {
        if (!map || infoWindow) return;
        const newInfoWindow = new google.maps.InfoWindow({
            content: contentString,
            maxWidth: 400,
            ariaLabel: "Uluru",
        });

        console.log("setting info window to ", newInfoWindow);

        setInfoWindow(newInfoWindow);
    
    }, [infoWindow, map]);
}


