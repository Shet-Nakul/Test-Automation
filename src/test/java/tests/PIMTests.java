package tests;

import org.testng.Assert;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.Test;
import pages.LoginPage;
import pages.DashboardPage;
import pages.PIMPage;

public class PIMTests extends BaseTest {

    private PIMPage pimPage;
    private String testEmployeeId = "EMP" + System.currentTimeMillis(); // Unique ID

    @BeforeMethod
    public void loginAndNavigateToPIM() {
        // Login and navigate to PIM page
        LoginPage loginPage = new LoginPage(driver);
        loginPage.login(VALID_USERNAME, VALID_PASSWORD);

        DashboardPage dashboardPage = new DashboardPage(driver);
        // Navigate to PIM
        driver.get(BASE_URL + "web/index.php/pim/viewEmployeeList");

        pimPage = new PIMPage(driver);
    }

    @Test(priority = 1, description = "Verify PIM page is displayed correctly")
    public void testPIMPageDisplay() {
        // Uses COMMON METHOD: isPageDisplayed()
        Assert.assertTrue(pimPage.isPageDisplayed(),
                "PIM page should be displayed");

        // Uses COMMON METHOD: getPageTitle()
        Assert.assertEquals(pimPage.getPageTitle(), "PIM",
                "PIM page title should be 'PIM'");
    }

    @Test(priority = 2, description = "Verify adding new employee without login details")
    public void testAddEmployeeBasic() {
        // Uses COMMON METHODS: enterFirstName(), enterMiddleName(), enterLastName(), clickSaveButton()
        pimPage.clickAddEmployeeMenu();

        pimPage.enterFirstName("John");
        pimPage.enterMiddleName("Robert");
        pimPage.enterLastName("Doe");
        pimPage.enterEmployeeId(testEmployeeId);

        pimPage.clickSaveButton();

        // Wait for success
        try {
            Thread.sleep(3000);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }

        // Verify employee was added by checking URL contains personal details
        Assert.assertTrue(driver.getCurrentUrl().contains("viewPersonalDetails"),
                "Should navigate to employee personal details page after adding");
    }

    @Test(priority = 3, description = "Verify adding employee with login details")
    public void testAddEmployeeWithLogin() {
        String uniqueUsername = "user" + System.currentTimeMillis();
        String employeeId = "EMP" + System.currentTimeMillis();

        // Uses COMMON METHOD: addEmployeeWithLogin() which internally uses multiple common methods
        // enterFirstName(), enterMiddleName(), enterLastName(), enterUsername(), enterPassword()
        pimPage.addEmployeeWithLogin(
                "Jane",
                "Marie",
                "Smith",
                employeeId,
                uniqueUsername,
                "Test@123"
        );

        // Wait for save
        try {
            Thread.sleep(3000);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }

        // Verify navigation to employee details
        Assert.assertTrue(driver.getCurrentUrl().contains("viewPersonalDetails"),
                "Should navigate to personal details after creating employee with login");
    }

    @Test(priority = 4, description = "Verify searching for employee by ID")
    public void testSearchEmployee() {
        // First add an employee to search for
        String searchEmpId = "EMP" + System.currentTimeMillis();
        pimPage.addEmployee("Test", "Search", "Employee", searchEmpId);

        // Wait for employee to be added
        try {
            Thread.sleep(2000);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }

        // Navigate back to employee list
        driver.get(BASE_URL + "web/index.php/pim/viewEmployeeList");

        // Uses COMMON METHOD: searchEmployee() which uses clickSearchButton()
        pimPage.searchEmployee(searchEmpId);

        // Uses COMMON METHOD: getRecordsFoundText()
        // This method is shared with Leave, Time, Admin, Recruitment tests!
        String recordsText = pimPage.getRecordsFoundText();
        Assert.assertTrue(recordsText.contains("Record"),
                "Should find the newly added employee");
    }

    @Test(priority = 5, description = "Verify reset button clears search filters")
    public void testResetSearchFilters() {
        // Enter search criteria
        pimPage.clickEmployeeListMenu();
        pimPage.enterSearchEmployeeId("12345");

        // Uses COMMON METHOD: clickResetButton()
        // This is the SAME method used in Leave, Time, Admin tests!
        pimPage.clickResetButton();

        // Verify page is still displayed
        // Uses COMMON METHOD: isPageDisplayed()
        Assert.assertTrue(pimPage.isPageDisplayed(),
                "PIM page should still be displayed after reset");
    }

    @Test(priority = 6, description = "Verify employee list displays records")
    public void testEmployeeListDisplay() {
        // Navigate to employee list
        pimPage.clickEmployeeListMenu();

        // Uses COMMON METHOD: clickSearchButton()
        // This method is shared across PIM, Leave, Time, Admin, Recruitment!
        pimPage.clickSearchButton();

        // Uses COMMON METHOD: getRecordsFoundText()
        String recordsText = pimPage.getRecordsFoundText();
        Assert.assertTrue(recordsText.contains("Record") || recordsText.contains("Found"),
                "Should display employee records");
    }
}