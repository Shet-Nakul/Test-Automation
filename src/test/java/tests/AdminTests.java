package tests;

import org.testng.Assert;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.Test;
import pages.LoginPage;
import pages.DashboardPage;
import pages.AdminPage;

public class AdminTests extends BaseTest {

    private AdminPage adminPage;

    @BeforeMethod
    public void loginAndNavigateToAdmin() {
        // Login and navigate to Admin page
        LoginPage loginPage = new LoginPage(driver);
        loginPage.login(VALID_USERNAME, VALID_PASSWORD);

        DashboardPage dashboardPage = new DashboardPage(driver);
        dashboardPage.navigateToAdmin();

        adminPage = new AdminPage(driver);
    }

    @Test(priority = 1, description = "Verify Admin page is displayed correctly")
    public void testAdminPageDisplay() {
        // Verify admin page is loaded
        Assert.assertTrue(adminPage.isAdminPageDisplayed(),
                "Admin page should be displayed");

        // Verify page title
        Assert.assertEquals(adminPage.getAdminPageTitle(), "Admin",
                "Admin page title should be 'Admin'");
    }

    @Test(priority = 2, description = "Verify Add button is displayed and clickable")
    public void testAddButtonFunctionality() {
        // Verify Add button is visible
        Assert.assertTrue(adminPage.isAddButtonDisplayed(),
                "Add button should be displayed on Admin page");

        // Click Add button
        adminPage.clickAddButton();

        // Verify navigation to add user page
        Assert.assertTrue(driver.getCurrentUrl().contains("saveSystemUser"),
                "Should navigate to Add User page");
    }

    @Test(priority = 3, description = "Verify user search functionality")
    public void testUserSearch() {
        // Search for admin user
        adminPage.enterSearchUsername("Admin");
        adminPage.clickSearchButton();

        // Wait for search results
        try {
            Thread.sleep(2000);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }

        // Verify records are found
        String recordsText = adminPage.getRecordsFoundText();
        Assert.assertTrue(recordsText.contains("Record"),
                "Search should return records containing 'Admin'");
    }
}