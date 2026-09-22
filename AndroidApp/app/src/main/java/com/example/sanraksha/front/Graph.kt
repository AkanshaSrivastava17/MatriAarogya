package com.example.sanraksha.front

import android.content.Context
import android.util.Log
import androidx.room.Room
import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase


object Graph {
    lateinit var database : PatientDataBase

    private val MIGRATION_7_8 = object : Migration(7, 8) {
        override fun migrate(db: SupportSQLiteDatabase) {
            db.execSQL(
                "ALTER TABLE vitals ADD COLUMN predicted_risk_label TEXT NOT NULL DEFAULT ''"
            )
        }
    }

    private val MIGRATION_8_9 = object : Migration(8, 9) {
        override fun migrate(db: SupportSQLiteDatabase) {
            db.execSQL(
                "ALTER TABLE `Patient-table` ADD COLUMN `patient-state` TEXT NOT NULL DEFAULT ''"
            )
        }
    }

    val patientRepository by lazy {
        PatientRepository(patientDao = database.patientDao())
    }

    val vitalsRepository by lazy{
        VitalsRepository(vitalsDao = database.vitalsDao())
    }


    fun provide(context: Context){
        try {
            database = Room.databaseBuilder(context, PatientDataBase::class.java, "patientlist.db")
                .addMigrations(MIGRATION_7_8, MIGRATION_8_9)
                .build()
        }catch (e: Exception) {
            Log.e("DB_ERROR", "Room DB init failed", e)
        }
    }

}