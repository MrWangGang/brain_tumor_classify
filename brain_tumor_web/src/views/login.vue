<template>
	<div class="flex items-center justify-center h-screen bg-gray-50">
		<div class="w-full max-w-sm space-y-4 p-6 bg-white rounded-2xl shadow-lg">
			<h1 class="text-xl font-semibold text-center">登录</h1>

			<input
				v-model="loginUsername"
				type="text"
				placeholder="用户名"
				class="w-full px-3 py-2 border rounded-lg"
			/>
			<input
				v-model="loginPassword"
				type="password"
				placeholder="密码"
				class="w-full px-3 py-2 border rounded-lg"
			/>
			<button @click="handleLogin" class="w-full bg-blue-500 text-white py-2 rounded-lg">
				登录
			</button>

			<button @click="showRegister = true" class="w-full border py-2 rounded-lg">
				注册
			</button>
		</div>

		<!-- 注册弹窗 -->
		<div v-if="showRegister" class="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
			<div class="bg-white w-full max-w-md p-6 rounded-2xl shadow-xl space-y-4">
				<h2 class="text-lg font-semibold">注册新用户</h2>

				<input v-model="registerForm.name" placeholder="姓名" class="w-full px-3 py-2 border rounded-lg" />
				<input v-model="registerForm.account" placeholder="账号" class="w-full px-3 py-2 border rounded-lg" />
				<input v-model="registerForm.password" type="password" placeholder="密码" class="w-full px-3 py-2 border rounded-lg" />
				<input v-model="registerForm.age" type="number" placeholder="年龄" class="w-full px-3 py-2 border rounded-lg" />
				<select v-model="registerForm.sex" class="w-full px-3 py-2 border rounded-lg">
					<option disabled value="">请选择性别</option>
					<option value="男">男</option>
					<option value="女">女</option>
				</select>

				<div class="flex justify-end space-x-2 pt-2">
					<button @click="showRegister = false" class="px-4 py-2 border rounded-lg">取消</button>
					<button @click="handleRegister" class="px-4 py-2 bg-green-500 text-white rounded-lg">提交注册</button>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import {ref} from 'vue'
import axios from 'axios'
import {useMessage} from "naive-ui";
import {defineStore} from 'pinia';
import {t} from "@/locales";
import {singleUserStore} from '@/utils/userStore'; // 假设文件名为 userStore.js 或 userStore.ts
import { useRouter } from 'vue-router'; // 引入 useRouter

const singleStore = singleUserStore();
const router = useRouter(); // 获取路由实例

const loginUsername = ref('')
const loginPassword = ref('')

const showRegister = ref(false)
const registerForm = ref({
	name: '',
	account: '',
	password: '',
	age: '',
	sex: '',
})
const ms = useMessage()

const handleLogin = async () => {
	try {
		const response = await axios.post('http://127.0.0.1:5000/login', {
			account: loginUsername.value,
			password: loginPassword.value
		});
		ms.success(response.data.message);
		singleStore.setUserId(response.data.id);
		router.push({ name: 'Chat' }); // 使用路由名称进行跳转
	} catch (error) {
		ms.error(error.response.data.message);
	}
}



const handleRegister = async () => {
	try {
		const response = await axios.post('http://127.0.0.1:5000/register', {
			name: registerForm.value.name,
			account: registerForm.value.account,
			password: registerForm.value.password,
			age: registerForm.value.age,
			sex: registerForm.value.sex
		})
		ms.success(response.data.message)
		showRegister.value = false
	} catch (error) {
		ms.error(error.response.data.message);
	}
}
</script>
