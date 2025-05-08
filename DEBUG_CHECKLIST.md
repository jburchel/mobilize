# Mobilize App Debugging Checklist

## Dashboard Page

- [x] Charts are not appearing
- [ ] Both View Pipeline buttons take considerable time to load the pages
- [x] The People page link (sidebar) takes forever to load the page
- [ ] The Churches page link (sidebar) takes forever to load
- [x] The Tasks page link (sidebar) takes you to the same 'Internal server error'
- [ ] The Communications page link (sidebar) same as above

## Sidebar

- [ ] It is not collapsable
- [ ] There is no logo

## Header (at the top of the page)

- [ ] The login dropdown does not show my picture

## People Page

- [ ] Takes too long to load (like a few seconds)
- [ ] Takes too long to load individual people when you click on them (a few seconds)
- [x] In the main list table the column for name shows None None all the way down
- [ ] In the same table the Pipeline Stage column is showing only PROMOTION for everyone even though in the Supabase database people have differing stages in the pipeline
- [ ] The delete icon for a person in the same table takes the user to the Internal server error page
- [ ] Some people don't open up when you click them (give Internal server error)... some do open up

## Pipeline Management Page

- [ ] When you click on the View Pipeline button it takes you to the right page, but all people (and churches) are showing up under Promotion
- [ ] When you click on the View Pipeline button it takes a VERY long time to load the page
- [ ] On the Main People Pipeline page you cannot click and drag people to other stages
- [ ] On the Main People Pipeline page the 3 dots beside each person that indicate a menu of some sort are not appearing as they should (they look like like something different... see screenshot)
- [ ] The same thing is true of the Churches Pipeline page as above (two items above)

## Google Sync Page

- [ ] When you click on contacts and it takes you to the contact page... you select contacts and then the 'Continue to Mapping' button is greyed out and you can't click it

## Reports Page

- [ ] The cards across the top of the page perpetually say 'LOADING'
- [ ] When you click on 'Create Custom Report' it does take you to the modal which you can complete, but when you click 'Generate Report' it takes you to the Internal server error page

## Email Management Page

- [ ] The Manage Templates button takes you to the Internal server error page
- [ ] Manage Signatures button is the same as above
- [ ] Manage Campaigns button does take you to the Email Campaigns page but when you click on New Campaign it takes you to the Internal server error page

## Settings Page

- [x] Seems to be working as expected

## Admin Panel (Dashboard)

- [ ] When you try to delete a user you get a lengthy error message
- [ ] System settings and Logs & Monitoring need to be hooked up (for a later iteration)
