// Resolve the platform sibling outside the router context: the router collects
// both .tsx and .web.tsx route files when exporting the web app.
export { default } from '@/components/native-pixel-entry';
