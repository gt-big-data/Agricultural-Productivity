import { ControlPosition, Map, MapControl } from "@vis.gl/react-google-maps";
import useDrawingManager from "./hooks/useDrawingManager";
import { useContext } from "react";
import { MapContext } from "./App";

function MainMap() {
    const _ = useDrawingManager();
    const [drawingManager, setDrawingManager] = useContext(MapContext);

    return (
        <div className="split left map">
            <Map
                defaultZoom={4}
                defaultCenter={{ lat: -33.860664, lng: 151.208138 }}
                onCameraChanged={(ev) =>
                    console.log('camera changed:', ev.detail.center, 'zoom:', ev.detail.zoom)
                }>
            </Map>
            <MapControl position={ControlPosition.TOP_CENTER}>
            </MapControl>
        </div>
    )
}

export default MainMap;