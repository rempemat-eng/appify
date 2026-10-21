# Recognising rest away from the phone

Claude L (gameplay mechanics), 21 Oct. **A proposal and a prototype behind a flag; desk research only. Nothing was tested on a phone.** Every number below is a proposal for Matt; changing how naps pay is a game-rule change.

## In short

- **Today** Dream Dust comes only from a nap the player starts, credited by the device clock, one Dream Dust a second (the demo clock). Nothing checks the phone: the game left open on the nap screen pays, a clock set forward pays the jump, a clock set back freezes the nap, and there is no cap.
- **Recommended: tier 0, on for everyone, no permissions.** Keep the declared nap (the player choosing to rest is the honest core) and measure it truthfully: time with the game open past a 60 s grace does not count, a clock set back re-anchors, a forgotten nap settles at 12 h, a day credits at most 16 h. Later, a small native module adds a monotonic clock (Android `elapsedRealtime`, iOS `CLOCK_MONOTONIC`) and the server stamps its own time, which closes clock changes while the app is away.
- **Tier 1, opt-in, later:** Android "quiet screen" (usage access, screen-off minutes computed on the device, only the number leaves it) as recognition, never as income the economy depends on. **iOS Screen Time: wait** (the Family Controls entitlement is uncertain for a game, takes weeks, and DeviceActivity thresholds misfired through iOS 26).
- **Not now:** Health sleep data (GDPR Article 9 health data), Focus status, iOS lock state (no public API), "come back" notifications (they work against the game).
- **Before any cap means anything** the demo rate (one Dream Dust a second) has to become a real rate. That is the Dream Dust decision in [dream-dust.md](dream-dust.md).

## The prototype (tier 0, off by default)

| Piece                                                                  | What                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| ---------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `lib/rest-recognition.ts`                                              | `recogniseNap()`: pure, no permissions. Foreground past the grace credits nothing; a clock set back re-anchors; per-nap and per-day caps. Units are the credited minutes `offline_seconds` counts                                                                                                                                                                                                                                                  |
| `lib/rest-flag.ts`, `lib/rest-flag-default.ts`, `lib/rest-flag.web.ts` | `REST_RECOGNITION`, false by default (read by the patch below once applied). On the web, `?rest=recognise` turns it on for a play-test, `?rest=today` off                                                                                                                                                                                                                                                                                          |
| `rest-recognition-game.patch`                                          | The wiring into `tick()`, ready for Codex, who owns `lib/game.ts` store logic (C42 on #149): behind the flag only, in a plain nap (`screen_off`, not missions), `tick()` credits what `recogniseNap()` returns, a clock set back re-anchors, and a module-level `foregroundSince` resets when a nap starts and when the app comes to the front. check:game passed with it applied; it is kept out of this PR so `lib/game.ts` stays with its owner |
| `lib/rest-recognition.test.ts`                                         | The rules above, in `npm run check:mechanics`                                                                                                                                                                                                                                                                                                                                                                                                      |

Not prototyped: the monotonic clock (needs a native module and a dev build), server time, the 2-minute minimum nap, and the copy ("Napping counts while NapAttack is closed. We don't see what else you do."). On the demo clock the 12 h cap is reached after 12 real minutes, so the caps only make sense once the rate is real.

## 1. What the app does today

The brief assumed the app counts the gap between sessions. **It does not.** Dream Dust comes only from a nap or mission that the player starts on purpose. The amount is wall-clock time from the device's own clock, and the app never checks whether the phone was actually put down.

- **A nap starts from a tap.** `sleep()` (`lib/game.ts:1544-1573`) sets `mode: 'screen_off'` (a plain nap or a "together" session) or `'mission'`. It also records `offStart` (the current `offline_seconds`), `offGrass` and `tickAt = Date.now()`.
- **A 1 s timer credits the time.** `startGame()` runs `tick()` every second (`lib/game.ts:1904`). In `tick()` (`lib/game.ts:1255-1275`), when `mode !== 'awake'`, it computes `elapsed = floor((end - tickAt)/1000)`. `end` is `Date.now()`, or the mission end for missions. That credit goes to:
  - `offline_seconds += elapsed` and `mood += elapsed` in every non-awake mode;
  - `grass` (Dream Dust) `+= elapsed`, **only in `'screen_off'`** (`:1272`). Missions pay their fixed `m.reward` when they complete (`:1277-1291`).
  - The rate is one Dream Dust per real second. The comment at `lib/offline-rules.ts:84` says "Offline MIN are existing demo seconds", and the UI labels them "SIMULATED MIN" (`components/game-overlays.tsx:521`).
- **Records are kept.** `recordOffline` splits the credited span across local midnights into per-day records (`lib/offline-rules.ts:85-105`). Each 15 credited seconds also earns a card (`lib/game.ts:1307-1314`). The daily goal and streak use 120 per day (`lib/offline-rules.ts:33-40,106-127`).
- **There is no check on what the phone did.** `tick()` has no `active` guard on the nap branch (`lib/game.ts:1257`), so a nap keeps paying while the app sits open in the foreground. Nothing checks other apps, the screen or the lock state. Leaving the app open on the nap screen and using another app pay exactly the same.
- **AppState is only used for these:**
  - Pausing the play budget, persisting and re-anchoring `tickAt` for an awake companion (`lib/game.ts:1908-1928`).
  - The web `visibilitychange` twin of the same (`:1929-1951`).
  - `useAppActive()` for decorative effects (`lib/app-active.ts:6-31`).
  - On return to the app, an awake player is re-anchored with `tickAt = now` (`:1920-1922`, also `:1158-1165` at load). So time between sessions in awake mode earns nothing.
- **The session gap is used in one place.** `lastActiveAt` is saved on backgrounding (`:1915`). `launchCareUntil` grants a 30 s "care" shield if the gap was 10 s or more (`lib/first-session.ts:21-22`).
- **Kills and reboots.** State goes to AsyncStorage (`lib/game.ts:662,1112`). After a kill or reboot, `init()` reloads `tickAt` and `mode`. The next `tick()` then credits the whole wall-clock gap since the nap started (`:1169`), so a nap survives a kill.
- **Changing the clock.** Every timestamp is `Date.now()`, so:
  - Setting the clock **forward** during a nap pays the whole jump immediately. Missions are capped at `mission_ends_at`; plain naps have no cap at all.
  - Setting it **backward** makes `seconds < 1` (`:1256`), so the nap freezes until the clock catches up. Nothing is lost, but nothing is earned either.
  - `player.last_seen` is the client's `Date.now()` (`:1422`, `lib/database.types.ts:90`), so the server holds no independent time.
  - The one exception is together sessions, which anchor `tickAt` to the server's `started_at` (`lib/game.ts:560,571`).
- **No caps.** There is no limit per nap or per day on Dream Dust from plain naps. `dailyProgress` clamps only the display (`lib/offline-rules.ts:35`).
- **Design pillar.** "Rest is the only engine. Walking, chatting and sparring are how you find and enjoy things, never how you farm them" (`docs/vision/cast.md:17`).

So today's signal is "the player declared a nap, and the device clock moved." Its cheat resistance is about zero, but it is honest about one thing: it never claims to have seen the player rest.

## 2. What the platforms offer

### 2.1 AppState, background state and clocks

- **What React Native reports** (RN 0.86 docs):
  - `active` "The app is running in the foreground".
  - `background` "...in another app / on the home screen / [Android] on another Activity".
  - `[iOS] inactive` "...transitioning between foreground & background, and during periods of inactivity such as entering the multitasking view, opening the Notification Center or in the event of an incoming call".
  - Android also has `blur` and `focus`.
  - **AppState cannot tell "screen off" from "using TikTok"**, and a killed app emits nothing at all. Persisted timestamps and the next launch are the only general mechanism.
- **Android clocks.** The `SystemClock` reference says:
  - The wall clock "can be set by the user or the phone network ... so the time may jump backwards or forwards unpredictably".
  - `uptimeMillis()` "stops when the system enters deep sleep".
  - `elapsedRealtime()` "return[s] the time since the system was booted, and include[s] deep sleep. This clock is guaranteed to be monotonic ... the recommend[ed] basis for general purpose interval timing".
  - `currentNetworkTimeClock()` (API 33) "cannot be adjusted by the user", but "may [sync] using an insecure network protocol, so the returned time should not be used for security purposes".
  - `ACTION_TIME_CHANGED` broadcasts are suggested for detecting clock changes.
- **iOS clocks.**
  - Swift `ContinuousClock` (iOS 16 and later) "always increments and does not stop incrementing while the system is asleep". Its instants are "only comparable locally", meaning within the same boot.
  - `ProcessInfo.systemUptime` is documented as "the time the system has been awake", which excludes sleep, so it is the **wrong** clock for this.
  - The native options are `ContinuousClock`, `mach_continuous_time()` or `clock_gettime(CLOCK_MONOTONIC)`. A forum thread (Sept 2024) quotes the man page: CLOCK_MONOTONIC "will continue to increment while the system is asleep".
- **Reboots reset monotonic clocks.** Spanning a reboot needs either a trusted remote time (the server) or acceptance that the wall clock is unverified for that span.
- **Expo coverage.** I found nothing in Expo SDK 57 that exposes a monotonic clock that includes sleep. The SDK 57 changelog (30 Jun 2026) mentions no such module.
  - `react-native-device-uptime` mixes iOS `systemUptime`, which excludes sleep, with Android `elapsedRealtime`, which includes it, so do not use it.
  - The clean route is a ~30-line local Expo Module: `elapsedRealtime()` on Android, `clock_gettime_nsec_np(CLOCK_MONOTONIC)` or `ContinuousClock` on iOS, plus a boot identifier. It needs a dev build, which the repo already has (`expo-dev-client` at `package.json:89`).
- **Web.** Only `document.visibilityState` and `performance.now()` exist. `performance.now()` is per page load, so it cannot span a closed tab.

### 2.2 iOS Screen Time APIs (FamilyControls, DeviceActivity, ManagedSettings)

- **Purpose.** FamilyControls is "Authorize your app to provide parental controls on a device."
  - Individual (self) authorization "requires approval from the owner of the device", followed by a biometric prompt.
  - Selections are opaque: `FamilyActivityPicker` lets "users specify applications, web domains, and categories without revealing their choices to the app."
- **Entitlement.**
  - The development capability is self-serve.
  - "To distribute your app ... request permission to use the com.apple.developer.family-controls entitlement ... If your app includes a Screen Time API app extension, submit the same request for the extension" (Apple, _Configuring Family Controls_).
  - DTS says: "You must request a Family Controls entitlement for every app and app extension that requires it."
  - There is no published review time. A developer reported 3+ weeks with no answer in May 2026 (forum thread 828085).
  - A consultant's write-up (16 Jun 2026) says Apple "has turned this entitlement down for apps that look like productivity tools, MDM, or employee monitoring". A game is not an obvious fit, so **approval is a real risk**.
- **What the app can read.**
  - `DeviceActivityReport` data stays inside the report extension. An Apple Frameworks Engineer said in Apr 2023: "moving Device Activity data outside of your extension's sandbox is not possible in order to preserve the user's privacy." The sandbox "prevents your extension from making network requests or moving sensitive content outside the extension's address space" (quoted in forum thread 795661).
  - The app can show a system-rendered chart but "cannot read the numbers, copy them out, or send them to a server" (drobinin.com).
  - What a game _can_ use is a `DeviceActivityMonitor` extension. It sets a schedule and a threshold event, for example "any app or category used ≥ N min during this nap window". It gets `intervalDidStart`, `intervalDidEnd` and `eventDidReachThreshold` callbacks.
  - In effect that is one bit per nap: "the threshold fired, or it didn't". The extension may write it to an App Group, which is the pattern `react-native-device-activity` uses.
- **Reliability (2026).**
  - DTS, Feb 2026: "This is a known issue in iOS 26, which is actively investigated." Thresholds were reaching "almost immediately".
  - A fix was reported in the iOS 26.5 beta (Apr 2026), but one developer says it "comes back ca. once per month".
  - Another report (5 Aug 2026) has a 10-minute threshold firing after about 5 minutes, also on iOS 18.
  - A 15-minute minimum schedule interval is widely repeated, but I found it only as a developer's claim, not in Apple's docs.
- **Expo support.**
  - [`react-native-device-activity`](https://github.com/kingstinct/react-native-device-activity) (Kingstinct) has an Expo config plugin with `appleTeamId` and `appGroup`, needs `expo prebuild` and `expo-build-properties`, and exposes `startMonitoring`, threshold events, `getEvents`, shields and pickers. Its JS listener works "only ... when the app is alive". `expo-app-blocker` is similar.
  - Both need a dev or production build. The `expo-app-blocker` README says "not available in Expo Go", and Family Controls (Development) builds "cannot be submitted to TestFlight or the App Store".

### 2.3 Android UsageStatsManager

- **Permission.** "Most methods on this API require the permission android.permission.PACKAGE_USAGE_STATS. However, declaring the permission implies intention to use the API and the user of the device still needs to grant permission through the Settings application. See Settings.ACTION_USAGE_ACCESS_SETTINGS. Methods which only return the information for the calling package do not require this permission. E.g. ... queryEventsForSelf."
- **Screen and lock events** (API 28 and later):
  - `SCREEN_INTERACTIVE` is "turned on for full user interaction".
  - `SCREEN_NON_INTERACTIVE` is "completely turned off or ... ambient display".
  - `KEYGUARD_SHOWN` is "keyguard has been shown, whether or not the screen is off".
  - `KEYGUARD_HIDDEN` is "typically ... when the user unlocks".
  - `DEVICE_SHUTDOWN` and `DEVICE_STARTUP` are API 29.
  - `queryEventStats` aggregates them per interval.
- **Limits.**
  - `queryEvents`: "Events are only kept by the system for a few days" and "Starting from Android R, if the user's device is not in an unlocked state ... null will be returned."
  - **Reading the nap window's screen-on/unlocked time when the app next opens is feasible, on-device and accurate.** No background service is needed.
- **Google Play policy.**
  - Restricted permissions include those "designated as Dangerous, Special, Signature", and usage access is a Special app access.
  - "Data accessed through Restricted Permissions is considered as personal and sensitive user data. The requirements of the User Data policy apply"
  - "Respect users' decisions if they decline ... You must make a reasonable effort to accommodate users who do not grant access"
  - Background or unexpected data use needs a "Prominent disclosure ... within the app itself ... Cannot only be placed in a privacy policy".
  - I did **not** find a usage-access declaration form (the QUERY_ALL_PACKAGES and SMS forms exist). Treat Play review as the deciding step, and expect questions.
- **Expo support.** I found no maintained Expo module for screen events. `react-native-app-usage-stats` and `@brighthustle/react-native-usage-stats-manager` cover per-app totals only, with no Expo plugin.
  - The README of the first warns that some OEMs return zero results unless battery optimisation is off.
  - A small local Expo Module is the realistic path: a manifest permission through a config plugin, `queryEvents` filtered to event types 15, 16, 17 and 18, and an intent to open the settings screen.
- **Digital Wellbeing** has no public read API. Its own numbers come from the same usage-stats store.

### 2.4 Other signals

| Signal               | Facts found                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| iOS lock state       | Quinn (DTS): "AFAIK there's no public API for determine the screen lock state of the device." `protectedDataWillBecomeUnavailable` is only about data protection ("a different thing"), and does not wake a suspended app. Undocumented Darwin keys are "considered private API".                                                                                                                                                                                                                  |
| Android lock state   | Usage events `KEYGUARD_*` (above). `ACTION_SCREEN_OFF` broadcasts reach only a running process (general knowledge, not checked here).                                                                                                                                                                                                                                                                                                                                                              |
| iOS Focus            | `INFocusStatusCenter` needs a user authorization and a "Privacy - Focus Status Usage Description". `isFocused` is only "true if Focus is enabled and this app isn't in its Allowed Apps list", and it does not say which Focus. The Intents-extension observer needs the **Communication Notifications** capability, which is meant for messaging and calling apps, so it does not fit a game.                                                                                                     |
| HealthKit sleep      | Users grant each read type separately. "An app isn't aware when the user denies permission to read data", and HealthKit data "may not [be] use[d] ... for advertising"; a privacy policy is required. Access is allowed only when "the use is for health or fitness purposes and this usage is clear in ... marketing text and ... user interface". The store "encrypts ... when the user locks the device", so background reads may fail. Expo: `@kingstinct/react-native-healthkit` (dev build). |
| Health Connect sleep | `android.permission.health.READ_SLEEP`. `react-native-health-connect` plus the `expo-health-connect` config plugin: "cannot be used in the Expo Go app". Its README says a Play declaration form is needed and approval "can take up to 7 days".                                                                                                                                                                                                                                                   |
| Local notifications  | `expo-notifications` is not installed. Apple 4.5.4 (text as quoted in Mar 2020): "Push Notifications must not be required for the app to function ... should not be used for promotions or direct marketing purposes unless customers have explicitly opted in". A "come back" nudge works against the game's purpose. An opt-in "your nap is done" alarm at a time the player chose is fine.                                                                                                      |

### 2.5 Store and privacy rules

- **Apple 5.1.1.**
  - "Apps should only request access to data relevant to the core functionality of the app and should only collect and use data that is required to accomplish the relevant task" (via a mirror, captured 9 Jun 2026; I could not fetch the guidelines page itself).
  - Privacy labels: "Data that is processed only on device is not 'collected' ... If you derive anything from that data and send it off device, the resulting data should be considered separately."
  - Rest minutes synced to the server count as _Product Interaction_ or _Other Usage Data_. Synced sleep data would count as _Health_.
- **App Review and Family Controls.** Any code path shaped like exporting usage data is a red flag (drobinin.com).
- **Google Play.** The restricted-permissions and User Data rules quoted above, prominent disclosure, and a usable app when the permission is declined.
- **GDPR.** Art. 9(1): processing "data concerning health ... shall be prohibited" unless, among other bases, Art. 9(2)(a) applies: "explicit consent ... for one or more specified purposes".
  - Sleep data is almost certainly health data.
  - Screen-on/off times are ordinary personal data, and behavioural. Keep them on the device and sync only the derived "credited minutes", which the app already syncs as `offline_seconds`.

## 3. Options compared

Effort is for one developer who knows Expo modules, without the store review wait.

| Signal                                                    | Platform                        | What it proves                                                   | Permission / entitlement                                                 | Expo support                                             | Store risk                                                  | Privacy cost                           | Effort                  | Cheat-resistance                                              |
| --------------------------------------------------------- | ------------------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------------ | -------------------------------------------------------- | ----------------------------------------------------------- | -------------------------------------- | ----------------------- | ------------------------------------------------------------- |
| Declared nap + wall clock (today)                         | all                             | Player tapped "nap"; clock moved                                 | none                                                                     | yes                                                      | none                                                        | none                                   | done                    | ~0 (clock change, keep using phone)                           |
| A. Declared nap + monotonic clock + server time + caps    | iOS, Android (web: server only) | Real time passed since the nap began                             | none                                                                     | small local Expo Module; web unchanged                   | none                                                        | none (no new data)                     | 1–3 days                | Stops clock changes; does **not** stop phone use              |
| B. App not in foreground during the nap                   | all                             | The game wasn't open (could be another app)                      | none                                                                     | AppState / visibility (exists)                           | none                                                        | none                                   | ~0.5 day                | Weak; stops "nap screen left open"                            |
| C. Android screen non-interactive / locked during the nap | Android 9+                      | The screen was off or locked for X of the window's minutes       | Usage access (Special); Play restricted-permission and User Data rules   | local Expo Module (none maintained)                      | medium (sensitive permission in a game; review questions)   | medium, if kept on device              | 3–5 days                | Strong for "phone down" (asleep with the screen on breaks it) |
| D. iOS DeviceActivity threshold during the nap            | iOS 16+                         | Selected apps or categories used < N min in the window (one bit) | Family Controls distribution for the app and the extension; Apple review | `react-native-device-activity` (config plugin, prebuild) | high (approval uncertain for a game; iOS 26 threshold bugs) | low (opaque; data stays in the system) | 1–2 weeks plus the wait | Medium–strong while it works; false "used" from OS bugs       |
| E. iOS lock state                                         | iOS                             | —                                                                | no public API                                                            | —                                                        | —                                                           | —                                      | —                       | not available                                                 |
| F. Focus status                                           | iOS 15+                         | A Focus that silences this app is on (not rest)                  | Focus authorization + Communication Notifications capability             | none maintained                                          | medium (capability misuse)                                  | low                                    | 3–5 days                | weak                                                          |
| G. Sleep from Health                                      | iOS / Android                   | Phone or watch logged sleep                                      | HealthKit / Health Connect + Play form                                   | community modules with plugins                           | medium                                                      | **high** (GDPR Art. 9 health data)     | 1 week                  | medium (self-entered sleep counts)                            |
| H. "Nap done" local notification                          | iOS / Android                   | nothing (it's a reminder)                                        | notification permission                                                  | `expo-notifications`                                     | low if opt-in                                               | low                                    | 1 day                   | n/a                                                           |

## 4. Recommended tiered design (least intrusive)

The rule throughout is that **rest is the only engine**. Every tier only _credits_ or _confirms_ rest. No tier takes Dream Dust away, adds a chore, or shames the player. Without the OS signals the game must still work fully (Play requires this, and it's kinder). All numbers below are **proposals for Matt to decide**, not current rules. Any change to the payout rules is a game-rule change and needs his sign-off.

### Tier 0: on by default, no permissions, all platforms

1. **Keep the declared nap**, since the player choosing to rest is the honest core. Then measure it robustly. When the nap starts and when the app goes to the background, save:
   - `wallAt = Date.now()`;
   - `monoAt`, from the native monotonic clock that includes sleep;
   - `bootId` (Android `Settings.Global.BOOT_COUNT`, or iOS boot time read with a tolerance);
   - the server time when it is reachable.

   On resume:
   - **same boot:** `credit = min(wallDelta, monoDelta)`. A forward clock jump is ignored silently.
   - **rebooted, or on web:** `credit = min(wallDelta, serverDelta)` if the server answers. Otherwise credit the wall delta up to the per-nap cap (proposal below) and confirm it against server time at the next sync.
   - **backward jump:** re-anchor `tickAt` instead of freezing the nap (this fixes the stall at `lib/game.ts:1256`).
   - The server should stamp its own `received_at` and not trust the client's `last_seen` (`lib/game.ts:1422`).

2. **Don't count time with the game open in the foreground** (option B). When `active` is true during a nap, pause accrual after a short grace period so the player can put the phone down.
   - _Proposal:_ a 60 s grace, then pause, with a gentle line from the companion ("i'll wait till you put me down").
   - This changes today's rule at `lib/game.ts:1257`, so it needs Matt's decision.
3. **Caps.** These keep a forgotten or faked nap from running away. All are _proposals_:
   - **Per nap:** credit at most **12 h** of real time. The nap then "settles", and the companion wakes on its own.
   - **Per local day:** at most **16 h** of credited rest. Sleep plus breaks fits within it, and a day can't exceed 24 h even across midnight splits.
   - **Minimum nap:** below **2 min** of real time, the companion just "blinks" and nothing is recorded. This removes taps that farm cards.
   - **Rate:** keep one curve that the player can see. Do _not_ add multipliers for longer naps, which would reward leaving the phone in a drawer rather than resting.
   - Note: the current rate is one Dream Dust per _second_, a demo rate. Real-time caps only mean something once the rate is set per real minute. Retuning the economy is a separate decision for Matt.
4. **Copy.** Be honest in the UI: "Napping counts while NapAttack is closed. We don't see what else you do." That is true today, and it remains true after Tier 0.

### Tier 1: opt-in, per platform, off by default, shown as a "garden blessing" and never required

- **Android: "Quiet screen" (option C).** After a full disclosure screen, the player grants Usage access.
  - When the app resumes, it reads `SCREEN_INTERACTIVE`, `SCREEN_NON_INTERACTIVE`, `KEYGUARD_SHOWN` and `KEYGUARD_HIDDEN` for the nap window only.
  - It computes `quietMinutes`, the minutes the screen was off or locked, and keeps the raw events on the device.
  - Only `quietMinutes` gets synced.
  - Reward this as _recognition_, not more income. A proposal: a visual "deep rest" mark on the receipt and a cosmetic garden touch, or at most a small bonus such as +10% on quiet minutes, capped by the Tier 0 caps. The economy should never depend on granting the permission.
  - If the read comes back null (the device is locked) or empty (OEM quirks), fall back to Tier 0 silently.
- **iOS: wait for now (option D).** The entitlement's chance of approval for a game is uncertain, it takes weeks, and DeviceActivity thresholds were unreliable through iOS 26 in 2026.
  - If it is pursued later, request the entitlement for the app and the monitor extension under a framing about the player's own wellbeing ("self-limit while napping").
  - Use one threshold, "any category ≥ 3 min during the nap" (a proposal).
  - Treat a threshold event only as a hint to validate against the monotonic clock, as developers do to work around the iOS 26 bug.
  - Never export usage data.
- **Notifications (H).** Offer an opt-in "wake me at…" local alarm that the player sets when starting a nap. Send no unprompted "come back" nudges or streak-loss warnings, because they work against the purpose.

### Tier 2: not recommended now

- **Health sleep data (G).** It brings in health data under GDPR Art. 9, HealthKit's "health or fitness purpose" rule and the Play health declaration. The benefit is only to recognise overnight sleep, which Tier 0 already credits when the player starts a nap before bed.
- **Focus status (F).** It is a weak signal, and the capability is meant for messaging apps.
- **iOS lock detection (E).** There is no public API for it.

### Platform and repo notes

- Every OS signal above needs a dev or production build (`expo-dev-client` is present). Expo Go and the web export get Tier 0 only.
- Per `AGENTS.md` and `docs/native-readiness.md`, put native calls in a local Expo Module guarded by `Platform.OS`, and give the web build a `.web.ts` stub.

## 5. Gaps and caveats

- No device testing was done. All behaviour comes from documentation and forum reports.
- Two Android reference pages were read with a direct download after the fetch tool's permission prompt timed out. I could not fetch the App Store Review Guidelines page itself, because a permission prompt timed out. Guideline 5.1.1 text comes from a third-party mirror captured 9 Jun 2026, and 4.5.4 from a March 2020 quote, so both should be checked against the live guidelines.
- I found no Google Play page that names `PACKAGE_USAGE_STATS` specifically. The policy reasoning applies the general Special and restricted-permission rules.
- The 15-minute DeviceActivity minimum interval is unverified. Whether the iOS 26.5 fix for thresholds actually shipped is unconfirmed.
- The claim that Android `ACTION_SCREEN_OFF` broadcasts need a running receiver comes from general knowledge, not a source.
- The iOS boot-identifier approach, `kern.boottime`, is referenced to the wall clock and shifts with clock changes. It needs a tolerance check, and that design is unproven.

## Sources

- React Native AppState 0.86: https://reactnative.dev/docs/0.86/appstate
- Android SystemClock: https://developer.android.com/reference/android/os/SystemClock
- Android UsageStatsManager: https://developer.android.com/reference/android/app/usage/UsageStatsManager
- Android UsageEvents.Event: https://developer.android.com/reference/android/app/usage/UsageEvents.Event
- Swift ContinuousClock: https://developer.apple.com/documentation/swift/continuousclock.md
- systemUptime and sleep (Swift Forums, Sept 2024): https://forums.swift.org/t/systemuptime-not-adequate-to-get-the-elapsed-realtime-since-boot/74350
- react-native-device-uptime: https://github.com/Luke-Rogerson/react-native-device-uptime
- Expo SDK 57 changelog: https://expo.dev/changelog/sdk-57.md
- Family Controls framework: https://developer.apple.com/documentation/familycontrols.md
- Configuring Family Controls: https://developer.apple.com/documentation/xcode/configuring-family-controls.md
- DTS, entitlement per extension: https://developer.apple.com/forums/thread/796550
- Distribution entitlement wait (May 2026): https://developer.apple.com/forums/thread/828085
- Device Activity data can't leave the sandbox (Apr 2023): https://developer.apple.com/forums/thread/727958
- Report extension sandbox wording: https://developer.apple.com/forums/thread/795661
- iOS 26 premature thresholds: https://developer.apple.com/forums/thread/814559 and https://developer.apple.com/forums/thread/840907
- Schedule interval claim: https://developer.apple.com/forums/thread/729841
- Building with Screen Time (16 Jun 2026): https://drobinin.com/consulting/screen-time-family-controls/building-with-screen-time-and-family-controls/
- react-native-device-activity: https://context7.com/kingstinct/react-native-device-activity
- expo-app-blocker README: https://cdn.jsdelivr.net/npm/expo-app-blocker@0.1.77/README.md
- react-native-app-usage-stats README: https://cdn.jsdelivr.net/npm/react-native-app-usage-stats@1.0.1/README.md
- @brighthustle/react-native-usage-stats-manager: https://npmjs.org/package/@brighthustle/react-native-usage-stats-manager
- Play, Permissions and APIs that Access Sensitive Information: https://support.google.com/googleplay/android-developer/answer/9888170
- Play, User Data and prominent disclosure: https://support.google.com/googleplay/android-developer/answer/10144311
- Play, QUERY_ALL_PACKAGES (contrast): https://support.google.com/googleplay/android-developer/answer/10158779
- iOS lock detection (Quinn): https://developer.apple.com/forums/thread/69333
- Focus status sample: https://developer.apple.com/documentation/usernotifications/handling-communication-notifications-and-focus-status-updates.md
- HealthKit privacy: https://developer.apple.com/documentation/healthkit/protecting-user-privacy.md
- Health Connect sleep: https://developer.android.com/health-and-fitness/health-connect/features/sleep-sessions
- react-native-health-connect README: https://unpkg.com/react-native-health-connect@3.5.3/README.md
- Apple App Privacy details: https://developer.apple.com/support/app-privacy-on-the-app-store/
- App Store 5.1.1 data minimisation (mirror): https://conductatlas.com/platform/apple/apple-app-store-review-guidelines/provision/CA-P-019060/apps-must-practice-data-minimization/
- App Store 4.5.4 (Mar 2020 quote): https://mjtsai.com/blog/2020/03/05/new-app-store-guidelines-for-push-notifications-and-more
- GDPR Art. 9: https://gdpr-text.com/read/article-9/
- Blocked or not fetched: https://developer.apple.com/app-store/review/guidelines/ (permission prompt timed out)
