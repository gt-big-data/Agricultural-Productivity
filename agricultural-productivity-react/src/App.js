import './App.css';
import { APIProvider, ControlPosition, Map, MapCameraChangedEvent, MapControl } from '@vis.gl/react-google-maps';
import MainMap from './MainMap';
import Sidebar from './Sidebar';
import { createContext, useState } from 'react';

export const MapContext = createContext();

function App() {
  const [drawingManager, setDrawingManager] = useState();

  return (
    <APIProvider apiKey={process.env.REACT_APP_GOOGLE_MAPS_API_KEY} onLoad={() => console.log('Maps API has loaded.')}>
      <MapContext.Provider value={[drawingManager, setDrawingManager]}>
        <MainMap />
        <Sidebar />
      </MapContext.Provider>
    </APIProvider>
  );
}



export default App;
