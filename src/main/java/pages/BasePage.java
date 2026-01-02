package pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import java.time.Duration;

public class BasePage {

    protected WebDriver driver;
    protected WebDriverWait wait;

    // Side Menu Locators
    protected By adminMenuItem = By.xpath("//span[text()='Admin']");
    protected By pimMenuItem = By.xpath("//span[text()='PIM']");
    protected By leaveMenuItem = By.xpath("//span[text()='Leave']");
    protected By timeMenuItem = By.xpath("//span[text()='Time']");
    protected By recruitmentMenuItem = By.xpath("//span[text()='Recruitment']");
    protected By performanceMenuItem = By.xpath("//span[text()='Performance']");
    protected By dashboardMenuItem = By.xpath("//span[text()='Dashboard']");
    protected By myInfoMenuItem = By.xpath("//span[text()='My Info']");
    protected By directoryMenuItem = By.xpath("//span[text()='Directory']");
    protected By maintenanceMenuItem = By.xpath("//span[text()='Maintenance']");
    protected By buzzMenuItem = By.xpath("//span[text()='Buzz']");

    // Top Bar Locators
    protected By userDropdown = By.className("oxd-userdropdown-tab");
    protected By logoutOption = By.xpath("//a[text()='Logout']");

    public BasePage(WebDriver driver) {
        this.driver = driver;
        this.wait = new WebDriverWait(driver, Duration.ofSeconds(10));
    }

    // Navigation Methods
    public void navigateToAdmin() {
        clickMenu(adminMenuItem);
    }

    public void navigateToPIM() {
        clickMenu(pimMenuItem);
    }

    public void navigateToLeave() {
        clickMenu(leaveMenuItem);
    }

    public void navigateToTime() {
        clickMenu(timeMenuItem);
    }

    public void navigateToRecruitment() {
        clickMenu(recruitmentMenuItem);
    }

    public void navigateToPerformance() {
        clickMenu(performanceMenuItem);
    }

    public void navigateToDashboard() {
        clickMenu(dashboardMenuItem);
    }

    protected void clickMenu(By locator) {
        wait.until(ExpectedConditions.elementToBeClickable(locator)).click();
    }

    public void logout() {
        wait.until(ExpectedConditions.elementToBeClickable(userDropdown)).click();
        wait.until(ExpectedConditions.elementToBeClickable(logoutOption)).click();
    }
    
    public boolean isAdminMenuVisible() {
        try {
            return driver.findElement(adminMenuItem).isDisplayed();
        } catch (Exception e) {
            return false;
        }
    }
}
