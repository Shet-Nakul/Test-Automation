package tests;

import org.testng.Assert;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.Test;
import pages.LoginPage;
import pages.DashboardPage;
import pages.LeavePage;

public class LeaveTests extends BaseTest {

    private LeavePage leavePage;

    @BeforeMethod
    public void loginAndNavigateToLeave() {
        // Login and navigate to Leave page
        LoginPage loginPage = new LoginPage(driver);
        loginPage.login(VALID_USERNAME, VALID_PASSWORD);

        DashboardPage dashboardPage = new DashboardPage(driver);
        // Navigate to Leave (clicking on Leave menu item)
        driver.get(BASE_URL + "web/index.php/leave/viewLeaveList");

        leavePage = new LeavePage(driver);
    }

    @Test(priority = 1, description = "Verify Leave page is displayed correctly")
    public void testLeavePageDisplay() {
        // Uses COMMON METHOD: isPageDisplayed()
        Assert.assertTrue(leavePage.isPageDisplayed(),
                "Leave page should be displayed");

        // Uses COMMON METHOD: getPageTitle()
        Assert.assertEquals(leavePage.getPageTitle(), "Leave",
                "Leave page title should be 'Leave'");
    }

    @Test(priority = 2, description = "Verify leave search by date range")
    public void testSearchLeaveByDateRange() {
        // Uses COMMON METHODS: enterFromDate(), enterToDate(), clickSearchButton()
        leavePage.enterFromDate("2024-01-01");
        leavePage.enterToDate("2024-12-31");
        leavePage.clickSearchButton();

        // Uses COMMON METHOD: getRecordsFoundText()
        String recordsText = leavePage.getRecordsFoundText();
        Assert.assertTrue(recordsText.contains("Record"),
                "Should display records found text");
    }

    @Test(priority = 3, description = "Verify reset button functionality")
    public void testResetButton() {
        // First enter some search criteria
        // Uses COMMON METHOD: searchByDateRange()
        leavePage.searchByDateRange("2024-01-01", "2024-12-31");

        // Uses COMMON METHOD: clickResetButton()
        leavePage.clickResetButton();

        // Verify form is reset (page is still displayed)
        // Uses COMMON METHOD: isPageDisplayed()
        Assert.assertTrue(leavePage.isPageDisplayed(),
                "Leave page should still be displayed after reset");
    }
}