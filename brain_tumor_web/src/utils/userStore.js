import { defineStore } from 'pinia';

export const singleUserStore = defineStore('user', {
	state: () => ({
		userId: localStorage.getItem('userId') || null
	}),
	actions: {
		setUserId(id) {
			this.userId = id;
			localStorage.setItem('userId', id || 'null'); // 保存到 localStorage
		},
		getUserId() {
			return this.userId;
		}
	}
});
