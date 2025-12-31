package pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import java.time.Duration;

public class AdminPage {

    private WebDriver driver;
    private WebDriverWait wait;

    // Locators
    private By adminHeader = By.xpath("//h6[text()='Admin']");
    private By addButton = By.xpath("//button[normalize-space()='Add']");
    private By searchUsernameField = By.xpath("(//input[@class='oxd-input oxd-input--active'])[2]");
    private By searchButton = By.xpath("//button[@type='submit']");
    private By userRoleDropdown = By.xpath("(//div[text()='-- Select --'])[1]");
    private By recordsFoundText = By.xpath("//span[contains(@class,'oxd-text--span')]");
    private By resetButton = By.xpath("//button[normalize-space()='Reset']");

    // Constructor
    public AdminPage(WebDriver driver) {
        this.driver = driver;
        this.wait = new WebDriverWait(driver, Duration.ofSeconds(10));
    }

    // Page Actions
    public boolean isAdminPageDisplayed() {
        try {
            return wait.until(ExpectedConditions.visibilityOfElementLocated(adminHeader)).isDisplayed();
        } catch (Exception e) {
            return false;
        }
    }

    public String getAdminPageTitle() {
        return wait.until(ExpectedConditions.visibilityOfElementLocated(adminHeader)).getText();
    }

    public void clickAddButton() {
        WebElement addBtn = wait.until(ExpectedConditions.elementToBeClickable(addButton));
        addBtn.click();
    }

    public void enterSearchUsername(String username) {
        WebElement searchField = wait.until(ExpectedConditions.visibilityOfElementLocated(searchUsernameField));
        searchField.clear();
        searchField.sendKeys(username);
    }

    public void clickSearchButton() {
        WebElement searchBtn = wait.until(ExpectedConditions.elementToBeClickable(searchButton));
        searchBtn.click();
    }

    public void searchUser(String username) {
        enterSearchUsername(username);
        clickSearchButton();
    }

    public boolean isAddButtonDisplayed() {
        try {
            return wait.until(ExpectedConditions.visibilityOfElementLocated(addButton)).isDisplayed();
        } catch (Exception e) {
            return false;
        }
    }

    public void clickUserRoleDropdown() {
        WebElement dropdown = wait.until(ExpectedConditions.elementToBeClickable(userRoleDropdown));
        dropdown.click();
    }

    public String getRecordsFoundText() {
        return wait.until(ExpectedConditions.visibilityOfElementLocated(recordsFoundText)).getText();
    }

    public void clickResetButton() {
        WebElement resetBtn = wait.until(ExpectedConditions.elementToBeClickable(resetButton));
        resetBtn.click();
    }

    public boolean isResetButtonDisplayed() {
        try {
            return driver.findElement(resetButton).isDisplayed();
        } catch (Exception e) {
            return false;
        }
    }
}