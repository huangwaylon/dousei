# UI Improvements Plan

## Overview
This document outlines the plan for improving the Train Commute Optimizer UI with three key enhancements:
1. Display only the selected route on the map when a user clicks a result
2. Reduce background map opacity to 60% for better route visibility
3. Collapse consecutive train line segments for simpler route viewing

## Current State Analysis

### Map Display Behavior
**Current Implementation:**
- File: [`main.js`](../web/public/src/main.js:119-140)
- When a candidate is clicked, the system:
  - Clears existing routes
  - Draws the selected candidate's routes with emphasis (opacity 0.8, weight 5)
  - Draws faded routes for other top 5 candidates (opacity 0.4, weight 3)
  - Zooms to the selected candidate station

**Issues:**
- Showing multiple routes creates visual clutter
- Makes it hard to focus on the specific route being examined
- Defeats the purpose of selecting a specific result

### Map Background Opacity
**Current Implementation:**
- File: [`map.js`](../web/public/src/map.js:29-34)
- Uses default OpenStreetMap tiles with no opacity modification
- Routes are drawn with opacity 0.4-0.8 and weight 3-5

**Issues:**
- Background map can compete visually with route lines
- Especially problematic in dense urban areas with many street details

### Route Details Display
**Current Implementation:**
- File: [`ui.js`](../web/public/src/ui.js:305-330)
- Each segment (station-to-station) is displayed individually
- Shows: railway line name, from/to stations, number of stops, travel time
- Transfer segments are marked separately

**Example Current Display:**
```
🚆 Tokyo Metro Hibiya Line
Roppongi → Hiroo
1 stops, 2.0 min

🚆 Tokyo Metro Hibiya Line
Hiroo → Ebisu
1 stops, 2.0 min

🚆 Tokyo Metro Hibiya Line
Ebisu → Nakameguro
1 stops, 2.0 min

🔄 Transfer
Nakameguro → Nakameguro
3.0 min transfer time

🚆 Tokyu Toyoko Line
Nakameguro → Yutenji
1 stops, 2.0 min
```

**Issues:**
- Repetitive display of same train line
- Takes up excessive vertical space
- Harder to get quick overview of the route
- Cognitive load to mentally combine segments

## Proposed Changes

### 1. Show Only Selected Route on Map

**Objective:** When user selects a route result, display only that route's train paths.

**Technical Approach:**
- File: [`main.js`](../web/public/src/main.js:119-140)
- Modify `handleCandidateClick()` function
- Remove the loop that draws faded routes for other candidates
- Keep only the selected candidate's route drawing

**Implementation:**
```javascript
function handleCandidateClick(index) {
  const candidate = ui.state.candidates[index];
  if (!candidate) return;

  ui.selectCandidate(index);
  
  // Clear existing routes
  map.clearRoutes();
  
  // Draw ONLY the selected candidate's routes
  map.drawCandidateRoutes(candidate, true);
  
  // Zoom to candidate
  map.zoomToStation(candidate.latitude, candidate.longitude, 13);
}
```

**Benefits:**
- Cleaner, focused map view
- User can clearly see the exact route they're considering
- Reduces visual noise and confusion
- Better alignment with user intent

### 2. Reduce Map Background Opacity

**Objective:** Make background map 60% opaque for better route visibility.

**Technical Approach:**
- File: [`map.js`](../web/public/src/map.js:29-34)
- Add `opacity: 0.6` to the tile layer options

**Implementation:**
```javascript
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  maxZoom: 18,
  minZoom: 9,
  opacity: 0.6  // Add this line
}).addTo(this.map);
```

**Benefits:**
- Route lines stand out more clearly
- Background context remains visible for orientation
- Professional appearance
- Reduced eye strain when focusing on routes

### 3. Collapse Consecutive Train Line Segments

**Objective:** Group consecutive segments on the same train line for cleaner display.

**Example Collapsed Display:**
```
🚆 Tokyo Metro Hibiya Line
Roppongi → Nakameguro
3 stops, 6.0 min

🔄 Transfer
Nakameguro → Nakameguro
3.0 min transfer time

🚆 Tokyu Toyoko Line
Nakameguro → Yutenji
1 stops, 2.0 min
```

**Technical Approach:**

#### A. Create Helper Function in ui.js
```javascript
/**
 * Collapse consecutive segments on the same train line
 * @param {Array} segments - Route segments to collapse
 * @returns {Array} Collapsed segments
 */
collapseSegments(segments) {
  if (!segments || segments.length === 0) return [];
  
  const collapsed = [];
  let currentGroup = null;
  
  for (const segment of segments) {
    // Transfers are always separate
    if (segment.is_transfer) {
      // Save current group if exists
      if (currentGroup) {
        collapsed.push(currentGroup);
        currentGroup = null;
      }
      // Add transfer as-is
      collapsed.push(segment);
      continue;
    }
    
    // Check if segment belongs to current group
    if (currentGroup && currentGroup.railway_name === segment.railway_name) {
      // Same line - extend the group
      currentGroup.to_station_name = segment.to_station_name;
      currentGroup.to_coordinates = segment.to_coordinates;
      currentGroup.num_stops += segment.num_stops;
      currentGroup.travel_time += segment.travel_time;
    } else {
      // Different line - save current and start new
      if (currentGroup) {
        collapsed.push(currentGroup);
      }
      currentGroup = {
        ...segment,
        is_collapsed: true
      };
    }
  }
  
  // Add final group
  if (currentGroup) {
    collapsed.push(currentGroup);
  }
  
  return collapsed;
}
```

#### B. Update renderRouteSegments in ui.js
- File: [`ui.js`](../web/public/src/ui.js:305-330)
- Call `collapseSegments()` before rendering
- Update the rendering logic to handle collapsed segments

**Implementation:**
```javascript
renderRouteSegments(segments) {
  if (!segments || segments.length === 0) {
    return '<div style="color: var(--color-text-secondary);">Direct connection</div>';
  }

  // Collapse consecutive segments on same line
  const collapsedSegments = this.collapseSegments(segments);

  return `
    <div class="route-segments">
      ${collapsedSegments.map(segment => `
        <div class="segment ${segment.is_transfer ? 'transfer' : ''}">
          <div class="segment-railway">
            ${segment.is_transfer ? '🔄 Transfer' : `🚆 ${segment.railway_name}`}
          </div>
          <div class="segment-stations">
            ${segment.from_station_name} → ${segment.to_station_name}
          </div>
          <div class="segment-info">
            ${segment.is_transfer 
              ? `${segment.travel_time.toFixed(1)} min transfer time` 
              : `${segment.num_stops} ${segment.num_stops === 1 ? 'stop' : 'stops'}, ${segment.travel_time.toFixed(1)} min`
            }
          </div>
        </div>
      `).join('')}
    </div>
  `;
}
```

**Benefits:**
- Reduced visual clutter in route details
- Easier to scan and understand routes at a glance
- Less scrolling required in modal
- Maintains all important information (line, endpoints, total stats)
- Transfers remain clearly visible as distinct actions

### CSS Updates (if needed)

The existing CSS in [`styles.css`](../web/public/src/styles.css:722-754) should work well with collapsed segments, but we may want to add subtle distinctions:

```css
/* Optional: Visual indicator for collapsed segments */
.segment.is-collapsed {
  /* Could add a subtle indicator that multiple stops are combined */
}
```

However, this is optional as the current styling is already clean and appropriate.

## User Experience Considerations

### 1. Map Route Selection
- **Before:** Multiple routes shown, hard to focus
- **After:** Only selected route shown, clear focus
- **UX Benefit:** Reduces cognitive load, clearer decision-making

### 2. Map Background
- **Before:** Opaque background competes with routes
- **After:** Subdued background enhances routes
- **UX Benefit:** Better visual hierarchy, professional appearance

### 3. Route Details
- **Before:** Verbose, repetitive station list
- **After:** Concise, grouped by train line
- **UX Benefit:** Faster comprehension, easier comparison between routes

## Edge Cases to Consider

### Route Display
1. **Single segment routes:** Should work fine, no collapsing needed
2. **All transfer segments:** Unlikely but handled (no collapsing)
3. **Complex routes with many transfers:** Collapsing makes these even more valuable

### Map Display
1. **No candidates selected:** Initial analysis still shows top 3 routes (unchanged)
2. **Clicking different candidates:** Properly clears and redraws only new selection
3. **Zooming/panning:** Map tiles maintain 60% opacity at all zoom levels

## Testing Plan

### Manual Testing Steps
1. **Map opacity:**
   - Load application
   - Verify background map is noticeably lighter
   - Confirm routes are more visible
   - Test at different zoom levels

2. **Route selection:**
   - Select two work stations
   - Run analysis
   - Click different candidate results
   - Verify only clicked route appears on map
   - Verify routes properly clear between selections

3. **Collapsed segments:**
   - View route details for various candidates
   - Verify consecutive same-line segments are collapsed
   - Verify transfers remain separate
   - Check stop counts and times are correctly summed
   - Test with simple routes (2-3 segments)
   - Test with complex routes (5+ segments, multiple transfers)

### Browser Compatibility
- Test in Chrome, Firefox, Safari
- Verify map rendering is consistent
- Check modal display and scrolling

## Implementation Order

1. **Map opacity** (Simplest, immediate visual improvement)
2. **Route selection** (Medium complexity, clear UX win)
3. **Segment collapsing** (Most complex, requires careful testing)

This order allows for incremental testing and validation.

## Success Criteria

- ✅ Background map displays at 60% opacity
- ✅ Only selected route displays on map when candidate clicked
- ✅ Route details group consecutive same-line segments
- ✅ All functionality remains working (no regressions)
- ✅ Visual improvements are clear and professional
- ✅ Route information remains accurate and complete

## Future Enhancements (Out of Scope)

- Color-code collapsed segments by train line
- Add train line icons/logos
- Collapsible/expandable segment details
- Show real-time delay information
- Route comparison view (side-by-side)

## Summary

These three focused improvements will significantly enhance the user experience by:
1. **Clarity:** Reducing visual noise on the map
2. **Focus:** Showing only relevant information when examining a route
3. **Efficiency:** Presenting route details in a more digestible format

All changes maintain the existing clean, modern design while making the application more user-friendly and professional.