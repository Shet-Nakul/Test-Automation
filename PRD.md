# Product Requirements Document (PRD): OrangeHRM Automation Suite Enhancement

## 1. Executive Summary
The goal of this project is to stabilize, correct, and align the automated test suite for the OrangeHRM application. The current suite contains commented-out tests, inconsistent navigation flows, and potential stability issues. We aim to bring the entire suite to a "running state" with well-designed, robust test cases.

## 2. Current State Analysis
- **Framework:** Java (JDK 21), Selenium WebDriver (4.39.0), TestNG (7.11.0), Maven.
- **Architecture:** Page Object Model (POM).
- **Status:**
  - `testng.xml` has major sections (Dashboard, Admin, Leave, Time, Recruitment, PIM) commented out.
  - `EmployeeLifecycleTests` uses direct URL navigation (`driver.get`) instead of simulating user menu clicks, breaking the realistic user flow.
  - Hardcoded `Thread.sleep` exists in some tests (e.g., `test03_AddNewEmployee`), leading to flakiness or slowness.
  - Test data management (unique IDs) is handled via `System.currentTimeMillis()`, which is acceptable for now but could be improved.

## 3. Objectives
1.  **Activate All Tests:** Uncomment and fix all test classes in `testng.xml`.
2.  **Align User Flows:** Refactor integration tests (e.g., `EmployeeLifecycleTests`) to navigate through the UI (Menu Clicks) rather than direct URL jumps.
3.  **Stability:** Replace `Thread.sleep` with Selenium `WebDriverWait` (Explicit Waits).
4.  **Maintainability:** Ensure strict adherence to the Page Object Model (POM). No driver actions should occur in Test classes.

## 4. Scope of Work

### 4.1. Configuration & Infrastructure
- Ensure `pom.xml` dependencies are compatible.
- Verify `BaseTest` properly handles browser lifecycle (setup/teardown) for both single tests and test suites.

### 4.2. Page Object Refactoring
- Review all Page Classes in `src/main/java/pages/`.
- Ensure common UI components (e.g., Side Menu, Top Bar) are handled in a `BasePage` or shared component, not duplicated.
- **Action:** Implement a `MenuNavigation` helper or method in `DashboardPage` (or a base page) to handle clicks to "Admin", "PIM", "Leave", etc.

### 4.3. Test Case Correction
#### Login & Dashboard
- Verify `LoginTests` covers valid, invalid, and forgot password scenarios.
- Verify `DashboardTests` checks for essential elements after login.

#### Module Tests (Admin, PIM, Leave, etc.)
- **Uncomment** these sections in `testng.xml`.
- **Debug & Fix:** Run each module independently. Fix locators (Selectors) if they have changed in the demo app.
- **Data Dependency:** Ensure tests that require data (e.g., "Search Employee") create that data first or handle the "No Records Found" case gracefully.

#### Integration Tests (`EmployeeLifecycleTests`)
- Refactor `test02_AddCandidate`, `test03_AddNewEmployee`, etc.
- **Requirement:** Change `driver.get(...)` to `dashboardPage.navigateToModule("Recruitment")`.
- Ensure `dependsOnMethods` logic is sound; if a dependent test fails, the subsequent ones should be skipped (default TestNG behavior) but the suite should continue gracefully.

## 5. Technical Requirements
- **Language:** Java 21
- **Test Runner:** TestNG
- **Browser:** Chrome (managed via WebDriverManager)
- **Reporting:** Console output (TestNG default) is sufficient for now; Allure/Extent reports are out of scope unless requested.

## 6. Acceptance Criteria
- [ ] `mvn test` executes without compilation errors.
- [ ] All tests defined in `testng.xml` are uncommented.
- [ ] Pass Rate: 100% (or known bugs documented).
- [ ] No `Thread.sleep` calls in the codebase (unless absolutely necessary and documented).
- [ ] `EmployeeLifecycleTests` flows mimic real user behavior (clicking menus).

## 7. Implementation Plan
1.  **Phase 1:** Enable and fix `LoginTests` and `DashboardTests`.
2.  **Phase 2:** Implement "Menu Navigation" methods in Page Objects.
3.  **Phase 3:** Refactor `EmployeeLifecycleTests` to use Menu Navigation.
4.  **Phase 4:** Enable `PIMTests` and `AdminTests`, fixing locators.
5.  **Phase 5:** Enable remaining modules (`Leave`, `Time`, `Recruitment`, `Performance`).
6.  **Phase 6:** Final Run & Polish.
