package tests;

import org.testng.Assert;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.Test;
import pages.LoginPage;
import pages.DashboardPage;
import pages.TimePage;

public class TimeTests extends BaseTest {

    private TimePage timePage;

    @BeforeMethod
    public void loginAndNavigateToTime() {
        // Login and navigate to Time page
        LoginPage loginPage = new LoginPage(driver);
        loginPage.login(VALID_USERNAME, VALID_PASSWORD);

        DashboardPage dashboardPage = new DashboardPage(driver);
        // Navigate to Time
        driver.get(BASE_URL + "web/index.php/time/viewEmployeeTimesheet");

        timePage = new TimePage(driver);
    }

    @Test(priority = 1, description = "Verify Time page is displayed correctly")
    public void testTimePageDisplay() {
        // Uses COMMON METHOD: isPageDisplayed()
        Assert.assertTrue(timePage.isPageDisplayed(),
                "Time page should be displayed");

        // Uses COMMON METHOD: getPageTitle()
        Assert.assertEquals(timePage.getPageTitle(), "Time",
                "Time page title should be 'Time'");

        // Verify menu items
        Assert.assertTrue(timePage.isTimesheetsMenuDisplayed(),
                "Timesheets menu should be displayed");
    }

    @Test(priority = 2, description = "Verify time search by date range")
    public void testSearchTimeByDateRange() {
        // Uses COMMON METHODS: enterFromDate(), enterToDate(), clickSearchButton()
        // These are the SAME methods used in LeaveTests!
        timePage.enterFromDate("2024-01-01");
        timePage.enterToDate("2024-12-31");
        timePage.clickSearchButton();

        // Uses COMMON METHOD: getRecordsFoundText()
        // This is the SAME method used in LeaveTests and AdminTests!
        String recordsText = timePage.getRecordsFoundText();
        Assert.assertTrue(recordsText.contains("Record") || recordsText.contains("No Records"),
                "Should display records status");
    }

    @Test(priority = 3, description = "Verify search and reset workflow")
    public void testSearchAndResetWorkflow() {
        // Uses COMMON METHOD: searchByDateRange()
        // This is the SAME method used in LeaveTests and RecruitmentTests!
        timePage.searchByDateRange("2024-06-01", "2024-06-30");

        try {
            Thread.sleep(1000);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }

        // Uses COMMON METHOD: clickResetButton()
        timePage.clickResetButton();

        // Uses COMMON METHOD: isPageDisplayed()
        Assert.assertTrue(timePage.isPageDisplayed(),
                "Time page should still be displayed after reset");
    }
}