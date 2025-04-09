import React from 'react';

// Placeholder component for the Main Menu / Dashboard page
function DashboardPage() {
    return (
        <div className="p-4 md:p-6">
            <h1 className="text-2xl font-bold text-primary mb-4">Main Menu</h1>
            {/* Replace placeholder content with actual dashboard elements */}
            <div className="bg-background p-4 rounded border border-table-border shadow-sm">
                <p className="text-font-color italic text-sm md:text-base">
                    Welcome! This dashboard page is currently under construction.
                </p>
                <p className="text-font-color mt-3 text-sm">Future content could include:</p>
                <ul className="list-disc list-inside mt-2 text-font-color text-sm space-y-1">
                    <li>Your recently accessed or modified pages</li>
                    <li>Quick actions (e.g., "Create New Page")</li>
                    <li>Summary of pending ToDo items</li>
                    <li>Notifications or system announcements</li>
                </ul>
            </div>
        </div>
    );
}

export default DashboardPage;