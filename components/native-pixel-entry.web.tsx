import { Redirect } from 'expo-router';

// Keep the web module graph and its existing Image/data-pixel renderer unchanged.
export default function NativePixelsRoute() {
  return <Redirect href="/" />;
}
