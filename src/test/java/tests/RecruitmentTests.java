package tests;

import org.testng.Assert;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.Test;
import pages.LoginPage;
import pages.DashboardPage;
import pages.RecruitmentPage;

public class RecruitmentTests extends BaseTest {

    private RecruitmentPage recruitmentPage;

    @BeforeMethod
    public void loginAndNavigateToRecruitment() {
        // Login and navigate to Recruitment page
        LoginPage loginPage = new LoginPage(driver);
        loginPage.login(VALID_USERNAME, VALID_PASSWORD);

        DashboardPage dashboardPage = new DashboardPage(driver);
        // Navigate to Recruitment
        driver.get(BASE_URL + "web/index.php/recruitment/viewCandidates");

        recruitmentPage = new RecruitmentPage(driver);
    }

    @Test(priority = 1, description = "Verify Recruitment page is displayed correctly")
    public void testRecruitmentPageDisplay() {
        // Uses COMMON METHOD: isPageDisplayed()
        Assert.assertTrue(recruitmentPage.isPageDisplayed(),
                "Recruitment page should be displayed");

        // Uses COMMON METHOD: getPageTitle()
        Assert.assertEquals(recruitmentPage.getPageTitle(), "Recruitment",
                "Recruitment page title should be 'Recruitment'");

        // Uses COMMON METHOD: isAddButtonDisplayed()
        // This is the SAME method used in AdminTests!
        Assert.assertTrue(recruitmentPage.isAddButtonDisplayed(),
                "Add button should be displayed");
    }

    @Test(priority = 2, description = "Verify Add button functionality")
    public void testAddButtonFunctionality() {
        // Uses COMMON METHOD: clickAddButton()
        // This is the SAME method used in AdminTests!
        recruitmentPage.clickAddButton();

        // Verify navigation to add candidate page
        Assert.assertTrue(driver.getCurrentUrl().contains("addCandidate"),
                "Should navigate to Add Candidate page");
    }

    @Test(priority = 3, description = "Verify candidate search by date range")
    public void testSearchCandidateByDateRange() {
        // Uses COMMON METHODS: enterFromDate(), enterToDate(), clickSearchButton()
        // These are the SAME methods used in LeaveTests and TimeTests!
        recruitmentPage.enterFromDate("2024-01-01");
        recruitmentPage.enterToDate("2024-12-31");
        recruitmentPage.clickSearchButton();

        // Uses COMMON METHOD: getRecordsFoundText()
        // This is the SAME method used in LeaveTests, TimeTests, and AdminTests!
        String recordsText = recruitmentPage.getRecordsFoundText();
        Assert.assertTrue(recordsText.contains("Record") || recordsText.contains("No Records"),
                "Should display records status");
    }
}