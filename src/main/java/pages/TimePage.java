package pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import java.time.Duration;

public class TimePage extends BasePage {

    // Locators
    private By timeHeader = By.xpath("//h6[text()='Time']");
    private By timesheetsMenu = By.xpath("//span[text()='Timesheets']");
    private By myTimesheetsOption = By.xpath("//a[text()='My Timesheets']");
    private By employeeTimesheetsOption = By.xpath("//a[text()='Employee Timesheets']");
    private By attendanceMenu = By.xpath("//span[text()='Attendance']");
    private By fromDateField = By.xpath("(//input[@placeholder='yyyy-dd-mm'])[1]");
    private By toDateField = By.xpath("(//input[@placeholder='yyyy-dd-mm'])[2]");
    private By searchButton = By.xpath("//button[@type='submit']");
    private By resetButton = By.xpath("//button[normalize-space()='Reset']");
    private By viewButton = By.xpath("//button[normalize-space()='View']");
    private By recordsFoundText = By.xpath("//span[contains(@class,'oxd-text--span')]");

    // Constructor
    public TimePage(WebDriver driver) {
        super(driver);
    }

    // COMMON METHOD: Used across multiple test classes
    public boolean isPageDisplayed() {
        try {
            return wait.until(ExpectedConditions.visibilityOfElementLocated(timeHeader)).isDisplayed();
        } catch (Exception e) {
            return false;
        }
    }

    // COMMON METHOD: Used across multiple test classes
    public String getPageTitle() {
        return wait.until(ExpectedConditions.visibilityOfElementLocated(timeHeader)).getText();
    }

    public void clickTimesheetsMenu() {
        WebElement timesheetsMenuItem = wait.until(ExpectedConditions.elementToBeClickable(timesheetsMenu));
        timesheetsMenuItem.click();
    }

    public void clickMyTimesheets() {
        clickTimesheetsMenu();
        WebElement myTimesheets = wait.until(ExpectedConditions.elementToBeClickable(myTimesheetsOption));
        myTimesheets.click();
    }

    public void clickEmployeeTimesheets() {
        clickTimesheetsMenu();
        WebElement empTimesheets = wait.until(ExpectedConditions.elementToBeClickable(employeeTimesheetsOption));
        empTimesheets.click();
    }

    public void clickAttendanceMenu() {
        WebElement attendanceMenuItem = wait.until(ExpectedConditions.elementToBeClickable(attendanceMenu));
        attendanceMenuItem.click();
    }

    // COMMON METHOD: Shared with LeavePage and RecruitmentPage
    public void enterFromDate(String date) {
        WebElement fromDate = wait.until(ExpectedConditions.visibilityOfElementLocated(fromDateField));
        fromDate.clear();
        fromDate.sendKeys(date);
    }

    // COMMON METHOD: Shared with LeavePage and RecruitmentPage
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

    public void clickViewButton() {
        WebElement viewBtn = wait.until(ExpectedConditions.elementToBeClickable(viewButton));
        viewBtn.click();
    }

    // COMMON METHOD: Shared with LeavePage and AdminPage
    public String getRecordsFoundText() {
        try {
            Thread.sleep(2000); // Wait for records to load
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
        return wait.until(ExpectedConditions.visibilityOfElementLocated(recordsFoundText)).getText();
    }

    public boolean isTimesheetsMenuDisplayed() {
        try {
            return driver.findElement(timesheetsMenu).isDisplayed();
        } catch (Exception e) {
            return false;
        }
    }

    public boolean isAttendanceMenuDisplayed() {
        try {
            return driver.findElement(attendanceMenu).isDisplayed();
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