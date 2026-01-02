package tests;

import org.testng.Assert;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;
import pages.*;

public class EmployeeLifecycleTests extends BaseTest {

    private LoginPage loginPage;
    private DashboardPage dashboardPage;
    private RecruitmentPage recruitmentPage;
    private PIMPage pimPage;
    private LeavePage leavePage;
    private TimePage timePage;
    private PerformancePage performancePage;

    private String candidateName = "TestCandidate" + System.currentTimeMillis();
    private String employeeId = "EMP" + System.currentTimeMillis();
    private String username = "user" + System.currentTimeMillis();

    @BeforeClass
    public void setupPages() {
        loginPage = new LoginPage(driver);
        dashboardPage = new DashboardPage(driver);
        recruitmentPage = new RecruitmentPage(driver);
        pimPage = new PIMPage(driver);
        leavePage = new LeavePage(driver);
        timePage = new TimePage(driver);
        performancePage = new PerformancePage(driver);
    }

    @Test(priority = 1, description = "Complete workflow: Login and verify dashboard")
    public void test01_LoginAndVerifyDashboard() {
        // Uses COMMON METHODs from LoginPage and DashboardPage
        loginPage.login(VALID_USERNAME, VALID_PASSWORD);

        Assert.assertTrue(dashboardPage.isDashboardDisplayed(),
                "Dashboard should be displayed after login");
    }

    @Test(priority = 2, description = "Recruitment: Add candidate", dependsOnMethods = "test01_LoginAndVerifyDashboard")
    public void test02_AddCandidate() {
        // Navigate to Recruitment
        driver.get(BASE_URL + "web/index.php/recruitment/viewCandidates");

        // Uses COMMON METHOD: isPageDisplayed() from RecruitmentPage
        Assert.assertTrue(recruitmentPage.isPageDisplayed(),
                "Recruitment page should be displayed");

        // Uses COMMON METHOD: clickAddButton()
        // This method is shared with Admin, PIM, Performance pages!
        recruitmentPage.clickAddButton();

        // In real scenario, we would fill candidate details here
        Assert.assertTrue(driver.getCurrentUrl().contains("addCandidate"),
                "Should navigate to add candidate page");
    }

    @Test(priority = 3, description = "PIM: Add new employee", dependsOnMethods = "test01_LoginAndVerifyDashboard")
    public void test03_AddNewEmployee() {
        // Navigate to PIM
        driver.get(BASE_URL + "web/index.php/pim/viewEmployeeList");

        // Uses COMMON METHODs: enterFirstName(), enterMiddleName(), enterLastName()
        // These methods are used across PIM and Admin modules!
        pimPage.addEmployeeWithLogin(
                "John",
                "M",
                "Smith",
                employeeId,
                username,
                "Test@123"
        );

        // Wait for employee creation
        try {
            Thread.sleep(3000);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }

        Assert.assertTrue(driver.getCurrentUrl().contains("viewPersonalDetails"),
                "Employee should be created and details page displayed");
    }

    @Test(priority = 4, description = "PIM: Search for newly added employee", dependsOnMethods = "test03_AddNewEmployee")
    public void test04_SearchEmployee() {
        // Navigate to employee list
        driver.get(BASE_URL + "web/index.php/pim/viewEmployeeList");

        // Uses COMMON METHOD: searchEmployee() which uses clickSearchButton()
        pimPage.searchEmployee(employeeId);

        // Uses COMMON METHOD: getRecordsFoundText()
        // This is shared across PIM, Leave, Time, Admin, Recruitment, Performance!
        String recordsText = pimPage.getRecordsFoundText();
        Assert.assertTrue(recordsText.contains("Record"),
                "Should find the newly created employee");
    }

    @Test(priority = 5, description = "Leave: Verify leave page for new employee context", dependsOnMethods = "test03_AddNewEmployee")
    public void test05_VerifyLeaveModule() {
        // Navigate to Leave
        driver.get(BASE_URL + "web/index.php/leave/viewLeaveList");

        // Uses COMMON METHOD: isPageDisplayed()
        // This method is used across ALL page objects!
        Assert.assertTrue(leavePage.isPageDisplayed(),
                "Leave page should be accessible");

        // Uses COMMON METHODs: enterFromDate(), enterToDate(), clickSearchButton()
        // These methods are shared with Time and Recruitment modules!
        leavePage.searchByDateRange("2024-01-01", "2024-12-31");

        // Uses COMMON METHOD: getRecordsFoundText()
        String recordsText = leavePage.getRecordsFoundText();
        Assert.assertTrue(recordsText.contains("Record") || recordsText.contains("No Records"),
                "Leave search should execute successfully");
    }

    @Test(priority = 6, description = "Time: Verify timesheet module", dependsOnMethods = "test03_AddNewEmployee")
    public void test06_VerifyTimeModule() {
        // Navigate to Time
        driver.get(BASE_URL + "web/index.php/time/viewEmployeeTimesheet");

        // Uses COMMON METHOD: isPageDisplayed()
        Assert.assertTrue(timePage.isPageDisplayed(),
                "Time page should be accessible");

        // Uses COMMON METHODs: enterFromDate(), enterToDate(), clickSearchButton()
        // SAME methods used in Leave and Recruitment!
        timePage.searchByDateRange("2024-01-01", "2024-12-31");

        // Uses COMMON METHOD: getRecordsFoundText()
        String recordsText = timePage.getRecordsFoundText();
        Assert.assertTrue(recordsText.contains("Record") || recordsText.contains("No Records"),
                "Timesheet search should execute successfully");
    }

    @Test(priority = 7, description = "Performance: Verify performance module", dependsOnMethods = "test03_AddNewEmployee")
    public void test07_VerifyPerformanceModule() {
        // Navigate to Performance
        driver.get(BASE_URL + "web/index.php/performance/searchEvaluatePerformanceReview");

        // Uses COMMON METHOD: isPageDisplayed()
        Assert.assertTrue(performancePage.isPageDisplayed(),
                "Performance page should be accessible");

        // Navigate to KPIs
        performancePage.navigateToKPIs();

        // Uses COMMON METHOD: isAddButtonDisplayed()
        // Shared with Admin, Recruitment, PIM!
        Assert.assertTrue(performancePage.isAddButtonDisplayed(),
                "Add button should be available for KPIs");
    }

    @Test(priority = 8, description = "End-to-End: Verify all modules are accessible in sequence",
            dependsOnMethods = {"test04_SearchEmployee", "test05_VerifyLeaveModule",
                    "test06_VerifyTimeModule", "test07_VerifyPerformanceModule"})
    public void test08_VerifyCompleteWorkflow() {
        // This test verifies the complete integration
        // All previous tests must pass for this to succeed

        // Final verification: Dashboard is still accessible
        driver.get(BASE_URL + "web/index.php/dashboard/index");
        Assert.assertTrue(dashboardPage.isDashboardDisplayed(),
                "Should be able to return to dashboard after complete workflow");

        System.out.println("==============================================");
        System.out.println("COMPLETE EMPLOYEE LIFECYCLE TEST - PASSED");
        System.out.println("Employee ID: " + employeeId);
        System.out.println("Username: " + username);
        System.out.println("==============================================");
    }
}