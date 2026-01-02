package pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import java.time.Duration;

public class PerformancePage extends BasePage {

    // Locators
    private By performanceHeader = By.xpath("//h6[text()='Performance']");
    private By configureMenu = By.xpath("//span[text()='Configure']");
    private By kpisMenu = By.xpath("//a[text()='KPIs']");
    private By trackersMenu = By.xpath("//a[text()='Trackers']");
    private By myReviewsMenu = By.xpath("//a[text()='My Reviews']");
    private By employeeReviewsMenu = By.xpath("//a[text()='Employee Reviews']");
    private By addButton = By.xpath("//button[normalize-space()='Add']");
    private By searchButton = By.xpath("//button[@type='submit']");
    private By resetButton = By.xpath("//button[normalize-space()='Reset']");
    private By recordsFoundText = By.xpath("//span[contains(@class,'oxd-text--span')]");
    private By kpiTitleField = By.xpath("(//input[@class='oxd-input oxd-input--active'])[2]");
    private By saveButton = By.xpath("//button[@type='submit']");
    private By reviewNameField = By.xpath("(//input[@class='oxd-input oxd-input--active'])[2]");

    // Constructor
    public PerformancePage(WebDriver driver) {
        super(driver);
    }

    // COMMON METHOD: Used across multiple test classes
    public boolean isPageDisplayed() {
        try {
            return wait.until(ExpectedConditions.visibilityOfElementLocated(performanceHeader)).isDisplayed();
        } catch (Exception e) {
            return false;
        }
    }

    // COMMON METHOD: Used across multiple test classes
    public String getPageTitle() {
        return wait.until(ExpectedConditions.visibilityOfElementLocated(performanceHeader)).getText();
    }

    public void clickConfigureMenu() {
        WebElement configMenu = wait.until(ExpectedConditions.elementToBeClickable(configureMenu));
        configMenu.click();
    }

    public void clickKPIsMenu() {
        clickConfigureMenu();
        WebElement kpisMenuItem = wait.until(ExpectedConditions.elementToBeClickable(kpisMenu));
        kpisMenuItem.click();
    }

    public void clickTrackersMenu() {
        clickConfigureMenu();
        WebElement trackersMenuItem = wait.until(ExpectedConditions.elementToBeClickable(trackersMenu));
        trackersMenuItem.click();
    }

    public void clickMyReviewsMenu() {
        WebElement myReviewsMenuItem = wait.until(ExpectedConditions.elementToBeClickable(myReviewsMenu));
        myReviewsMenuItem.click();
    }

    public void clickEmployeeReviewsMenu() {
        WebElement empReviewsMenuItem = wait.until(ExpectedConditions.elementToBeClickable(employeeReviewsMenu));
        empReviewsMenuItem.click();
    }

    // COMMON METHOD: Shared with Admin, Recruitment, PIM
    public void clickAddButton() {
        WebElement addBtn = wait.until(ExpectedConditions.elementToBeClickable(addButton));
        addBtn.click();
    }

    // COMMON METHOD: Used across multiple test classes
    public void clickSearchButton() {
        WebElement searchBtn = wait.until(ExpectedConditions.elementToBeClickable(searchButton));
        searchBtn.click();
    }

    // COMMON METHOD: Used across multiple test classes
    public void clickResetButton() {
        WebElement resetBtn = wait.until(ExpectedConditions.elementToBeClickable(resetButton));
        resetBtn.click();
    }

    // COMMON METHOD: Shared with Leave, Time, Admin, Recruitment, PIM tests
    public String getRecordsFoundText() {
        try {
            Thread.sleep(2000); // Wait for records to load
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
        return wait.until(ExpectedConditions.visibilityOfElementLocated(recordsFoundText)).getText();
    }

    // COMMON METHOD: Shared with multiple modules
    public void clickSaveButton() {
        WebElement saveBtn = wait.until(ExpectedConditions.elementToBeClickable(saveButton));
        saveBtn.click();
    }

    public void enterKPITitle(String title) {
        WebElement titleField = wait.until(ExpectedConditions.visibilityOfElementLocated(kpiTitleField));
        titleField.clear();
        titleField.sendKeys(title);
    }

    public void enterReviewName(String reviewName) {
        WebElement nameField = wait.until(ExpectedConditions.visibilityOfElementLocated(reviewNameField));
        nameField.clear();
        nameField.sendKeys(reviewName);
    }

    // COMMON METHOD: Shared with Admin, Recruitment
    public boolean isAddButtonDisplayed() {
        try {
            return wait.until(ExpectedConditions.visibilityOfElementLocated(addButton)).isDisplayed();
        } catch (Exception e) {
            return false;
        }
    }

    public boolean isConfigureMenuDisplayed() {
        try {
            return driver.findElement(configureMenu).isDisplayed();
        } catch (Exception e) {
            return false;
        }
    }

    public boolean isMyReviewsMenuDisplayed() {
        try {
            return driver.findElement(myReviewsMenu).isDisplayed();
        } catch (Exception e) {
            return false;
        }
    }

    // Combined method for navigating to KPIs
    public void navigateToKPIs() {
        clickConfigureMenu();
        clickKPIsMenu();
    }

    // Combined method for creating KPI
    public void createKPI(String title) {
        navigateToKPIs();
        clickAddButton();
        enterKPITitle(title);
        clickSaveButton();
    }
}