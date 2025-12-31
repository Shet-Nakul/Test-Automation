package tests;

import org.testng.Assert;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.Test;
import pages.LoginPage;
import pages.DashboardPage;

public class DashboardTests extends BaseTest {

    private DashboardPage dashboardPage;

    @BeforeMethod
    public void login() {
        // Login before each test
        LoginPage loginPage = new LoginPage(driver);
        loginPage.login(VALID_USERNAME, VALID_PASSWORD);
        dashboardPage = new DashboardPage(driver);
    }

    @Test(priority = 1, description = "Verify dashboard elements are displayed")
    public void testDashboardElementsDisplayed() {
        // Verify dashboard is displayed
        Assert.assertTrue(dashboardPage.isDashboardDisplayed(),
                "Dashboard should be displayed");

        // Verify Quick Launch section
        Assert.assertTrue(dashboardPage.isQuickLaunchSectionDisplayed(),
                "Quick Launch section should be visible");

        // Verify Admin menu is visible
        Assert.assertTrue(dashboardPage.isAdminMenuVisible(),
                "Admin menu should be visible for admin user");
    }

    @Test(priority = 2, description = "Verify navigation to Admin page")
    public void testNavigateToAdminPage() {
        // Navigate to Admin page
        dashboardPage.navigateToAdmin();

        // Verify URL contains 'admin'
        Assert.assertTrue(driver.getCurrentUrl().contains("admin"),
                "Should navigate to admin page");
    }

    @Test(priority = 3, description = "Verify logout functionality")
    public void testLogout() {
        LoginPage loginPage = new LoginPage(driver);

        // Perform logout
        dashboardPage.logout();

        // Wait for login page and verify we're back on login page
        try {
            Thread.sleep(2000); // Wait for logout animation
        } catch (InterruptedException e) {
            e.printStackTrace();
        }

        Assert.assertTrue(driver.getCurrentUrl().contains("login") ||
                        driver.getCurrentUrl().equals(BASE_URL),
                "Should return to login page after logout");
    }
}