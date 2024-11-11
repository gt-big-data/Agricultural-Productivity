import { useContext } from "react";
import { MapContext } from "./App";
function Sidebar() {
    const [drawingManager, _] = useContext(MapContext);

    return (
        <div className="split right sidebar">
            <p> Proceed with selected region? </p>
            <div button="button">
                <button onClick={() => {
                    drawingManager.setMap(null);
                    
                }}>
                    Proceed </button>
            </div>
        </div>
    )

}

export default Sidebar;