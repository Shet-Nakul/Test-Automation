package pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import java.time.Duration;
import java.util.List;

public class LeavePage {

    private WebDriver driver;
    private WebDriverWait wait;

    // Locators
    private By leaveHeader = By.xpath("//h6[text()='Leave']");
    private By applyButton = By.xpath("//a[text()='Apply']");
    private By myLeaveButton = By.xpath("//a[text()='My Leave']");
    private By leaveListButton = By.xpath("//a[text()='Leave List']");
    private By fromDateField = By.xpath("(//input[@placeholder='yyyy-dd-mm'])[1]");
    private By toDateField = By.xpath("(//input[@placeholder='yyyy-dd-mm'])[2]");
    private By searchButton = By.xpath("//button[@type='submit']");
    private By resetButton = By.xpath("//button[normalize-space()='Reset']");
    private By leaveTypeDropdown = By.xpath("(//div[@class='oxd-select-text-input'])[1]");
    private By recordsFoundText = By.xpath("//span[contains(@class,'oxd-text--span')]");

    // Constructor
    public LeavePage(WebDriver driver) {
        this.driver = driver;
        this.wait = new WebDriverWait(driver, Duration.ofSeconds(10));
    }

    // COMMON METHOD: Used across multiple test classes
    public boolean isPageDisplayed() {
        try {
            return wait.until(ExpectedConditions.visibilityOfElementLocated(leaveHeader)).isDisplayed();
        } catch (Exception e) {
            return false;
        }
    }

    // COMMON METHOD: Used across multiple test classes
    public String getPageTitle() {
        return wait.until(ExpectedConditions.visibilityOfElementLocated(leaveHeader)).getText();
    }

    public void clickApplyButton() {
        WebElement applyBtn = wait.until(ExpectedConditions.elementToBeClickable(applyButton));
        applyBtn.click();
    }

    public void clickMyLeaveButton() {
        WebElement myLeaveBtn = wait.until(ExpectedConditions.elementToBeClickable(myLeaveButton));
        myLeaveBtn.click();
    }

    public void clickLeaveListButton() {
        WebElement leaveListBtn = wait.until(ExpectedConditions.elementToBeClickable(leaveListButton));
        leaveListBtn.click();
    }

    // COMMON METHOD: Used in Leave, Time, and Recruitment tests
    public void enterFromDate(String date) {
        WebElement fromDate = wait.until(ExpectedConditions.visibilityOfElementLocated(fromDateField));
        fromDate.clear();
        fromDate.sendKeys(date);
    }

    // COMMON METHOD: Used in Leave, Time, and Recruitment tests
    public void enterToDate(String date) {
        WebElement toDate = wait.until(ExpectedConditions.visibilityOfElementLocated(toDateField));
        toDate.clear();
        toDate.sendKeys(date);
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

    // COMMON METHOD: Used in Leave, Time, Admin tests
    public String getRecordsFoundText() {
        try {
            Thread.sleep(2000); // Wait for records to load
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
        return wait.until(ExpectedConditions.visibilityOfElementLocated(recordsFoundText)).getText();
    }

    public void clickLeaveTypeDropdown() {
        WebElement dropdown = wait.until(ExpectedConditions.elementToBeClickable(leaveTypeDropdown));
        dropdown.click();
    }

    public boolean isApplyButtonDisplayed() {
        try {
            return driver.findElement(applyButton).isDisplayed();
        } catch (Exception e) {
            return false;
        }
    }

    // COMMON METHOD: Used for date range search in multiple modules
    public void searchByDateRange(String fromDate, String toDate) {
        enterFromDate(fromDate);
        enterToDate(toDate);
        clickSearchButton();
    }
}