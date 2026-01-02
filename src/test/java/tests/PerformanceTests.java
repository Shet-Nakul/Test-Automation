package tests;

import org.testng.Assert;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.Test;
import pages.LoginPage;
import pages.DashboardPage;
import pages.PerformancePage;

public class PerformanceTests extends BaseTest {

    private PerformancePage performancePage;

    @BeforeMethod
    public void loginAndNavigateToPerformance() {
        // Login and navigate to Performance page
        LoginPage loginPage = new LoginPage(driver);
        loginPage.login(VALID_USERNAME, VALID_PASSWORD);

        DashboardPage dashboardPage = new DashboardPage(driver);
        // Navigate to Performance
        driver.get(BASE_URL + "web/index.php/performance/searchEvaluatePerformanceReview");

        performancePage = new PerformancePage(driver);
    }

    @Test(priority = 1, description = "Verify Performance page is displayed correctly")
    public void testPerformancePageDisplay() {
        // Uses COMMON METHOD: isPageDisplayed()
        // This is the SAME method used across ALL page objects!
        Assert.assertTrue(performancePage.isPageDisplayed(),
                "Performance page should be displayed");

        // Uses COMMON METHOD: getPageTitle()
        Assert.assertEquals(performancePage.getPageTitle(), "Performance",
                "Performance page title should be 'Performance'");
    }

    @Test(priority = 2, description = "Verify Configure menu and navigation")
    public void testConfigureMenuNavigation() {
        // Verify Configure menu is displayed
        Assert.assertTrue(performancePage.isConfigureMenuDisplayed(),
                "Configure menu should be displayed");

        // Navigate to KPIs
        performancePage.clickConfigureMenu();
        performancePage.clickKPIsMenu();

        // Verify navigation to KPIs page
        Assert.assertTrue(driver.getCurrentUrl().contains("searchKpi"),
                "Should navigate to KPIs page");
    }

    @Test(priority = 3, description = "Verify My Reviews menu is displayed")
    public void testMyReviewsMenuDisplay() {
        // Verify My Reviews menu exists
        Assert.assertTrue(performancePage.isMyReviewsMenuDisplayed(),
                "My Reviews menu should be displayed");

        // Click My Reviews
        performancePage.clickMyReviewsMenu();

        // Verify navigation
        Assert.assertTrue(driver.getCurrentUrl().contains("myPerformanceReview"),
                "Should navigate to My Reviews page");
    }

    @Test(priority = 4, description = "Verify KPI page displays add button")
    public void testKPIPageAddButton() {
        // Navigate to KPIs
        performancePage.navigateToKPIs();

        // Uses COMMON METHOD: isAddButtonDisplayed()
        // This is the SAME method used in Admin, Recruitment, PIM tests!
        Assert.assertTrue(performancePage.isAddButtonDisplayed(),
                "Add button should be displayed on KPIs page");

        // Uses COMMON METHOD: clickAddButton()
        // This method is shared with Admin, Recruitment, PIM!
        performancePage.clickAddButton();

        // Verify navigation to add KPI form
        Assert.assertTrue(driver.getCurrentUrl().contains("saveKpi"),
                "Should navigate to add KPI page");
    }

    @Test(priority = 5, description = "Verify search functionality on KPIs page")
    public void testSearchKPIs() {
        // Navigate to KPIs
        performancePage.navigateToKPIs();

        // Uses COMMON METHOD: clickSearchButton()
        // This is the SAME method used in PIM, Leave, Time, Admin, Recruitment!
        performancePage.clickSearchButton();

        // Wait for results
        try {
            Thread.sleep(2000);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }

        // Uses COMMON METHOD: getRecordsFoundText()
        // This is shared across 6 different modules!
        String recordsText = performancePage.getRecordsFoundText();
        Assert.assertTrue(recordsText.contains("Record") || recordsText.contains("No Records"),
                "Should display search results");
    }

    @Test(priority = 6, description = "Verify reset button functionality")
    public void testResetButtonOnKPIs() {
        // Navigate to KPIs
        performancePage.navigateToKPIs();

        // Perform search first
        performancePage.clickSearchButton();

        try {
            Thread.sleep(1000);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }

        // Uses COMMON METHOD: clickResetButton()
        // This is the SAME method used in PIM, Leave, Time, Admin!
        performancePage.clickResetButton();

        // Verify page is still displayed
        // Uses COMMON METHOD: isPageDisplayed()
        Assert.assertTrue(performancePage.isPageDisplayed(),
                "Performance page should still be displayed after reset");
    }
}