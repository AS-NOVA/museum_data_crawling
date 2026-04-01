![](.files/%E6%95%B4%E7%90%86%E4%B8%BAPPS%E6%A0%BC%E5%BC%8F%E8%BF%87%E7%A8%8B/nbGAmLlg4QhRtgA.png)

数据主要依据为`museumschina.cn\data\data_final_20260312_211455.csv`，应在其基础上更新

根据上表，需要整理的列如下：

| 新列名                             | 来源                       |
| ---------------------------------- | -------------------------- |
| id                                 | 【待询问】                 |
| name                               | name                       |
| era                                | 新石器时代                 |
| period                             | 【尽量从name提取】         |
| currentLocation_country            | 中国                       |
| currentLocation_province           | 【从museum获取】           |
| currentLocation_city               | 【从museum获取】           |
| currentLocation_district           | 【从museum获取】           |
| currentLocation_specificAddress    | 【从museum获取】           |
| currentLocation_coordinate         | 【从museum获取】           |
| sourceCitation_sourceId            | 博物中国                   |
| sourceCitation_locator             | url                        |
| sourceCitation_locatorType         | URL                        |
| collectionInfo_collectorName       | 袁承进                     |
| collectionInfo_collectorId         | 【待询问】                 |
| collectionInfo_collectedTime_year  | 2026年                     |
| collectionInfo_collectedTime_month | 3月                        |
| collectionInfo_collectedTime_day   | 5日                        |
| images_id[list]                    | 【待询问】                 |
| images_url[list]                   | all_images_paths           |
| images_extension[list]             | 【从all_images_paths提取】 |
| images_name[list]                  | 【待询问】                 |
| images_description[list]           | 【可填哪个是主图】         |

以上操作将在

