package pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import java.time.Duration;

public class DashboardPage {

    private WebDriver driver;
    private WebDriverWait wait;

    // Locators
    private By dashboardHeader = By.xpath("//h6[text()='Dashboard']");
    private By userDropdown = By.className("oxd-userdropdown-tab");
    private By logoutOption = By.xpath("//a[text()='Logout']");
    private By adminMenuItem = By.xpath("//span[text()='Admin']");
    private By pimMenuItem = By.xpath("//span[text()='PIM']");
    private By timeWidget = By.xpath("//p[text()='Time at Work']");
    private By quickLaunchSection = By.xpath("//p[text()='Quick Launch']");

    // Constructor
    public DashboardPage(WebDriver driver) {
        this.driver = driver;
        this.wait = new WebDriverWait(driver, Duration.ofSeconds(10));
    }

    // Page Actions
    public boolean isDashboardDisplayed() {
        try {
            return wait.until(ExpectedConditions.visibilityOfElementLocated(dashboardHeader)).isDisplayed();
        } catch (Exception e) {
            return false;
        }
    }

    public String getDashboardTitle() {
        return wait.until(ExpectedConditions.visibilityOfElementLocated(dashboardHeader)).getText();
    }

    public void clickUserDropdown() {
        WebElement dropdown = wait.until(ExpectedConditions.elementToBeClickable(userDropdown));
        dropdown.click();
    }

    public void logout() {
        clickUserDropdown();
        WebElement logoutBtn = wait.until(ExpectedConditions.elementToBeClickable(logoutOption));
        logoutBtn.click();
    }

    public void navigateToAdmin() {
        WebElement adminMenu = wait.until(ExpectedConditions.elementToBeClickable(adminMenuItem));
        adminMenu.click();
    }

    public void navigateToPIM() {
        WebElement pimMenu = wait.until(ExpectedConditions.elementToBeClickable(pimMenuItem));
        pimMenu.click();
    }

    public boolean isTimeWidgetDisplayed() {
        try {
            return wait.until(ExpectedConditions.visibilityOfElementLocated(timeWidget)).isDisplayed();
        } catch (Exception e) {
            return false;
        }
    }

    public boolean isQuickLaunchSectionDisplayed() {
        try {
            return driver.findElement(quickLaunchSection).isDisplayed();
        } catch (Exception e) {
            return false;
        }
    }

    public boolean isAdminMenuVisible() {
        try {
            return driver.findElement(adminMenuItem).isDisplayed();
        } catch (Exception e) {
            return false;
        }
    }
}