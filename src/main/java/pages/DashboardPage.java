package pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import java.time.Duration;

public class DashboardPage extends BasePage {

    // Locators
    private By dashboardHeader = By.xpath("//h6[text()='Dashboard']");
    private By timeWidget = By.xpath("//p[text()='Time at Work']");
    private By quickLaunchSection = By.xpath("//p[text()='Quick Launch']");

    // Constructor
    public DashboardPage(WebDriver driver) {
        super(driver);
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
    
    public void clickUserDropdown() {
        wait.until(ExpectedConditions.elementToBeClickable(userDropdown)).click();
    }
}