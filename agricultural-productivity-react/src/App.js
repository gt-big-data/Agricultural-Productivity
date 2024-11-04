import './App.css';
import { APIProvider, ControlPosition, Map, MapCameraChangedEvent, MapControl } from '@vis.gl/react-google-maps';
import MainMap from './MainMap';

function App() {

  return (
    <APIProvider apiKey={process.env.REACT_APP_GOOGLE_MAPS_API_KEY} onLoad={() => console.log('Maps API has loaded.')}>
      <MainMap />
    </APIProvider>
  );
}



export default App;
