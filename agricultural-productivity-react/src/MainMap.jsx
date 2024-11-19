import { ControlPosition, InfoWindow, Map, MapControl, Marker, useMap, useMarkerRef } from "@vis.gl/react-google-maps";
import useDrawingManager from "./hooks/useDrawingManager";
import { useContext } from "react";
import { MapContext } from "./App";
import coordinates from './hooks/useDrawingManager';
import useInfoWindow from "./hooks/useInfoWindow";


function MainMap() {
    const _ = useDrawingManager();
    const __ = useInfoWindow();

    const [drawingManager, setDrawingManager, infoWindow, setInfoWindow, markerPosition, setMarkerPosition] = useContext(MapContext);
    const map = useMap();

    const [markerRef, setMarkerRef] = useMarkerRef();

    console.log({ infoWindow })

    if (markerPosition) {
        console.log({"lat": markerPosition["Gh"]["lo"], "lng": markerPosition["Gh"]["hi"] })
    }

    return (
        <div className="map">
            <Map
                defaultZoom={4}
                defaultCenter={{ lat: -33.860664, lng: 151.208138 }}
                onCameraChanged={(ev) =>
                    console.log('camera changed:', ev.detail.center, 'zoom:', ev.detail.zoom)
                }>
            </Map>

            {/* <InfoWindow
                headerContent={contentString}
                maxWidth={200}
                ariaLabel={"Selected Region"}
            >
            </InfoWindow> */}

            {markerPosition ?

                <Marker
                    ref={markerRef}
                    position={{"lat": (markerPosition["ei"]["lo"] + markerPosition["ei"]["hi"]) / 2, "lng": (markerPosition["Gh"]["lo"] + markerPosition["Gh"]["hi"]) / 2 }}
                    onClick={() => {
                        console.log("i clicked yippeee");
                        infoWindow.open(({
                            anchor: markerRef,
                            content: "Hello",
                            map
                        }))

                        infoWindow.setPosition({"lat": (markerPosition["ei"]["lo"] + markerPosition["ei"]["hi"]) / 2, "lng": (markerPosition["Gh"]["lo"] + markerPosition["Gh"]["hi"]) / 2 })
                    }}
                >
                </Marker> : <></>
            }



            <MapControl position={ControlPosition.TOP_CENTER}>
            </MapControl>

        </div>
    )
}

export default MainMap;