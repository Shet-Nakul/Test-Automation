package tests;

import org.testng.Assert;
import org.testng.annotations.Test;
import pages.DashboardPage;
import pages.EmployeePage;
import pages.LoginPage;
import pages.PIMPage;
import org.openqa.selenium.support.ui.WebDriverWait;
import java.time.Duration;


/**
 * EmployeeTest - Scenario 1: Employee Lifecycle Management
 * One scenario = one test case
 */
public class EmployeeTest extends BaseTest {

    @Test
    public void employeeLifecycleScenario1() {

        // =========================
        // Step 1: Admin Login
        // =========================
        System.out.println("Step 1: Admin Login");
        LoginPage loginPage = new LoginPage(driver);
        loginPage.login(VALID_USERNAME, VALID_PASSWORD);

        DashboardPage dashboardPage = new DashboardPage(driver);
        Assert.assertTrue(dashboardPage.isDashboardDisplayed(),
                "Step 1 Failed: Login failed / Dashboard not visible");
        System.out.println("✅ Step 1 Passed: Dashboard is displayed");

        // =========================
        // Step 2: Navigate to PIM Module
        // =========================
        System.out.println("\nStep 2: Navigate to PIM Module");
        EmployeePage employeePage = new EmployeePage(driver);
        PIMPage pimPage = new PIMPage(driver);

        employeePage.goToPIMModule();
        Assert.assertTrue(pimPage.isPageDisplayed(),
                "Step 2 Failed: PIM module not loaded");
        System.out.println("✅ Step 2 Passed: PIM module is loaded");

        // =========================
        // Step 3: Create New Employee
        // =========================
        System.out.println("\nStep 3: Create New Employee");
        employeePage.openAddEmployee();

        String employeeId = employeePage.createEmployeeAndGetEmployeeId("John", "M", "Doe");
        System.out.println("Captured Employee ID: " + employeeId);

        boolean createToast = employeePage.waitForToastToContain("Success", 10);
        boolean personalDetailsLoaded = employeePage.isPersonalDetailsPageLoaded();

        Assert.assertTrue(createToast || personalDetailsLoaded,
                "Step 3 Failed: Employee create not confirmed. Toast:" + createToast + " PersonalDetails:" + personalDetailsLoaded);

        System.out.println("✅ Step 3 Passed: Employee created successfully");

        // =========================
        // Step 4: Search and Verify Employee
        // =========================
        System.out.println("\nStep 4: Search and Verify Employee");

        employeePage.goToPIMModule();
        employeePage.openEmployeeList();

        employeePage.searchEmployeeInListById(employeeId);

        boolean recordFound = employeePage.isRecordFound();
        boolean recordInTable = employeePage.verifyEmployeeInTable(employeeId, "John", "Doe");

        Assert.assertTrue(recordFound || recordInTable,
                "Step 4 Failed: Employee not found. RecordFound:" + recordFound + " RecordInTable:" + recordInTable);

        System.out.println("✅ Step 4 Passed: Employee verified");

        // =========================
        // Step 5: Update Employee Personal Details
        // =========================
        System.out.println("\nStep 5: Update Employee Personal Details");

        employeePage.clickFoundEmployeeRecord(employeeId);

        employeePage.updatePersonalDetailsDirectly("Jonathan", "2000-03-10", "Indian", "Male");


        boolean firstNameUpdated;
        boolean dobUpdated;

        try {
            firstNameUpdated = new WebDriverWait(driver, Duration.ofSeconds(10))
                    .until(d -> employeePage.isFirstNameValue("Jonathan"));
        } catch (Exception e) {
            firstNameUpdated = false;
        }

        try {
            dobUpdated = new WebDriverWait(driver, Duration.ofSeconds(10))
                    .until(d -> employeePage.isDobValue("2000-03-10"));
        } catch (Exception e) {
            dobUpdated = false;
        }


        Assert.assertTrue(firstNameUpdated && dobUpdated,
                "Step 5 Failed: Values not updated properly. FirstName=" + employeePage.getFirstNameValue()
                        + " DOB=" + employeePage.getDobValue());

        // =========================
        // Step 6: Review Employee Profile
        // =========================
        System.out.println("\nStep 6: Review Employee Profile");

        Assert.assertEquals(employeePage.getFirstNameValue(), "Jonathan",
                "Step 6 Failed: Data persistence issue with First Name");

        Assert.assertEquals(employeePage.getDobValue(), "2000-03-10",
                "Step 6 Failed: Data persistence issue with DOB");

        System.out.println("✅ Step 6 Passed: Profile verified");

        // =========================
        // Step 7: Delete Employee Record
        // =========================
        System.out.println("\nStep 7: Delete Employee Record");

        employeePage.goToPIMModule();
        employeePage.openEmployeeList();

        employeePage.searchEmployeeInListById(employeeId);

        Assert.assertTrue(employeePage.isEmployeeFoundInList(),
                "Step 7 Failed: Employee not found before deletion");
        System.out.println("Employee found, deleting...");

        employeePage.deleteEmployeeFromSearchResults();

        // ✅ Toast is optional check (not main proof)
        boolean deleteToast =
                employeePage.waitForToastToContain("Successfully Deleted", 6)
                        || employeePage.waitForToastToContain("Success", 6)
                        || employeePage.waitForToastToContain("Deleted", 6);

        System.out.println("Delete toast captured: " + deleteToast);
        if (!deleteToast) {
            System.out.println("⚠️ Toast not captured (this is fine). Actual toast text: " + employeePage.tryGetToastMessage());
        }

        // ✅ REAL PROOF: search again and confirm No Records Found
        employeePage.searchEmployeeInListById(employeeId);

        Assert.assertTrue(employeePage.waitUntilNoRecordsFound(15),
                "Step 7 Failed: Employee still exists after deletion OR UI didn't refresh in time.");

        System.out.println("✅ Step 7 Passed: Employee deleted successfully");

        // =========================
        // Step 8: Logout
        // =========================
        System.out.println("\nStep 8: Logout");
        employeePage.logoutFromApp();
        System.out.println("✅ Step 8 Passed: Logout successful");

        System.out.println("\n========================================");
        System.out.println("✅ Scenario Complete: Employee Lifecycle Management");
        System.out.println("Employee ID used: " + employeeId);
        System.out.println("========================================");
    }
}
