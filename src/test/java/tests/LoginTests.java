package tests;

import org.testng.Assert;
import org.testng.annotations.Test;
import pages.LoginPage;
import pages.DashboardPage;

public class LoginTests extends BaseTest {

    @Test(priority = 1, description = "Verify successful login with valid credentials")
    public void testValidLogin() {
        LoginPage loginPage = new LoginPage(driver);
        DashboardPage dashboardPage = new DashboardPage(driver);

        // Perform login
        loginPage.enterUsername(VALID_USERNAME);
        loginPage.enterPassword(VALID_PASSWORD);
        loginPage.clickLoginButton();

        // Verify dashboard is displayed
        Assert.assertTrue(dashboardPage.isDashboardDisplayed(),
                "Dashboard should be displayed after successful login");
        Assert.assertEquals(dashboardPage.getDashboardTitle(), "Dashboard",
                "Dashboard title should be 'Dashboard'");
    }

    @Test(priority = 2, description = "Verify login fails with invalid credentials")
    public void testInvalidLogin() {
        LoginPage loginPage = new LoginPage(driver);

        // Attempt login with invalid credentials
        loginPage.enterUsername("InvalidUser");
        loginPage.enterPassword("InvalidPassword");
        loginPage.clickLoginButton();

        // Verify error message is displayed
        Assert.assertTrue(loginPage.isErrorMessageDisplayed(),
                "Error message should be displayed for invalid login");
        Assert.assertTrue(loginPage.getErrorMessage().contains("Invalid credentials"),
                "Error message should mention invalid credentials");
    }

    @Test(priority = 3, description = "Verify forgot password link is displayed and clickable")
    public void testForgotPasswordLink() {
        LoginPage loginPage = new LoginPage(driver);

        // Verify forgot password link is visible
        Assert.assertTrue(loginPage.isForgotPasswordLinkDisplayed(),
                "Forgot password link should be displayed on login page");

        // Click forgot password link
        loginPage.clickForgotPassword();

        // Verify URL changed (password reset page)
        Assert.assertTrue(driver.getCurrentUrl().contains("requestPasswordResetCode"),
                "Should navigate to password reset page");
    }
}