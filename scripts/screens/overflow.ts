/** Serialized by Playwright into the page. Keep this function self-contained. */
export function screenOverflow(current: string): string[] {
  const problems: string[] = [];
  if (
    document.documentElement.scrollWidth > innerWidth + 1 ||
    document.body.scrollWidth > innerWidth + 1
  )
    problems.push(
      `Document width ${Math.max(document.documentElement.scrollWidth, document.body.scrollWidth)} > viewport ${innerWidth}`,
    );
  for (const element of document.querySelectorAll<HTMLElement>('body *')) {
    const style = getComputedStyle(element);
    const rect = element.getBoundingClientRect();
    if (
      rect.width <= 0 ||
      rect.height <= 0 ||
      rect.right <= 0 ||
      rect.left >= innerWidth ||
      rect.bottom <= 0 ||
      rect.top >= innerHeight ||
      style.visibility === 'hidden' ||
      style.display === 'none'
    )
      continue;
    if (
      ['auto', 'scroll'].includes(style.overflowX) &&
      element.scrollWidth > element.clientWidth + 1
    ) {
      // MissionDestinationMap deliberately has six horizontal destination buttons.
      // Match the entire semantic set, not dimensions, a generic DIV or all Missions
      // overflow. Level gates append a label but do not change the destination.
      const destinations = [
        'LIBRARY',
        'MOUNTAIN',
        'PARK',
        "MOSS'S STALL",
        'SPARRING RING',
        'HOME GARDEN',
      ];
      const labels = Array.from(element.querySelectorAll('[role="button"]'), (button) =>
        button.getAttribute('aria-label')?.replace(/ · LV \d+$/, ''),
      );
      const missionRail =
        current === 'missions' &&
        labels.length === destinations.length &&
        destinations.every((label) => labels.filter((value) => value === label).length === 1);
      // A wider document or an overflowing vertical sheet must still fail.
      const intentionalRail =
        style.overflowY === 'hidden' &&
        (missionRail ||
          (current === 'companions' &&
            element.querySelectorAll('[role="button"][aria-label^="Preview "]').length > 1) ||
          (current === 'battle' &&
            element.querySelectorAll('[role="button"][aria-label$="tap to select"]').length > 0));
      if (intentionalRail) continue;
      problems.push(
        `${element.getAttribute('aria-label') ?? element.getAttribute('role') ?? element.tagName}: horizontal scroll ${element.scrollWidth} > ${element.clientWidth}`,
      );
    }
  }
  return problems;
}
