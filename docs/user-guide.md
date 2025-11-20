# OpenShift Checks Web - The User Guide

---

## Home 
![Home](/docs/assets/home_blank.png)    

### Last Check Results   

- Select cluster name from combo-box, then press "Run cluster checks" button.   

    ![Last Check Results](/docs/assets/home-select-cluster.png)   

#### View the results in the table as following:   

##### Runtime Metadata
  The parameters below are essential for basic information about check run:
  * `when` - the timestamp    
  * `title` - the title of checks(scripts) collection

  ![Results - Runtime Metadata](/docs/assets/home-results-metadata.png)   

---

##### Report    
    List actual output of each check

![Results - Report](/docs/assets/home-results-report.png)   

### Settings: 
Defines OpenShit cluster connection attributes: 

![Home-Settings](/docs/assets/home-settings.png) 

The cluster connection is managed using `Add New Credential`, `Edit Credential`, and `Delete Credential` buttons.
In order to Edit or Delete, the row from credential table must be selected first.

- Create credential pop-up:

![Home-Settings-Add-Credential](/docs/assets/home-settings-add-creds.png)  

- Edit Credential pop-up:   

![Home-Settings-Edit-Credential](/docs/assets/home-settings-edit-creds.png)  

- Delete Credential pop-up:   

![Home-Settings-Delete-Credential](/docs/assets/home-settings-delete-creds.png)  

---

## Scheduler

### Job List    

![Scheduler-JobList](/docs/assets/scheduler-joblist.png)

#### Create Job
![Scheduler-JobList](/docs/assets/scheduler-create-job.png)


### Settings    
![Scheduler-JobList](/docs/assets/scheduler-settings.png  )

---

## Editor

While based on OSS Monaco editor, this one was customized to work with shell scripts including code completion.

* The left pane:
            
1. Its file tree where directory can be selected from the combo-box on the left top of the editor window. 
2. The name of the check script.

* The right pane:
3. The source code editor    
4. The code completion
5. Toolbar with followong functionalities:
`New`, `Save`, `Reload`, `Delete`, `Minimap`, `Terminal`
6. Cluster selector 

![Editor-Tree-Sctipt](/docs/assets/editor-job-list.png)  


---